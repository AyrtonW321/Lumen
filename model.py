"""PyTorch lead scorer: predicts the chance the next touch on a lead goes well (interested, email request, booked).

How it works, step by step:
1. lumen.features() turns each lead into ~20 numbers between 0 and 1 (attempts, voicemail streak, brand, ...).
2. Each past call becomes one training example: features *before* the call -> 1 if the call went well, else 0.
   Your Good/Poor buttons add extra examples with 3x weight.
3. A PyTorch model learns weights that turn features into a probability.
4. HIDDEN = 0 makes the model logistic regression: one nn.Linear layer, the smallest neural network.
   Each weight then says how much a feature pushes the score up or down, so the app can explain scores.
   Set HIDDEN = 16 to get a real hidden layer (an MLP). Only do that once you have thousands of calls,
   and keep it only if its validation Brier score beats the logistic version.
"""
import torch
from torch import nn

HIDDEN = 0            # 0 = logistic regression; >0 = one hidden layer with this many neurons
EPOCHS = 400          # passes over the training data
LEARNING_RATE = 0.05
WEIGHT_DECAY = 1e-2   # L2 penalty: keeps weights small so the model can't memorize a few leads
MIN_EXAMPLES = 20
VALIDATION_EVERY = 5  # every 5th lead is held out to check the model on leads it never saw


class LeadNet(nn.Module):
    def __init__(self, n_features, hidden=HIDDEN):
        super().__init__()
        if hidden == 0:
            self.net = nn.Linear(n_features, 1)
        else:
            self.net = nn.Sequential(nn.Linear(n_features, hidden), nn.ReLU(), nn.Linear(hidden, 1))

    def forward(self, x):
        # Returns logits (raw scores). torch.sigmoid(logit) turns them into probabilities.
        return self.net(x).squeeze(-1)


class Scorer:
    def __init__(self, net, names, metrics):
        self.net, self.names, self.metrics = net, names, metrics

    @classmethod
    def train(cls, X, y, w, lead_ids=None):
        """X: list of feature dicts, y: list of 0/1, w: list of example weights, lead_ids: for the holdout split."""
        if len(X) < MIN_EXAMPLES or len(set(y)) < 2:
            raise ValueError(f"need at least {MIN_EXAMPLES} examples with both good and poor results "
                             f"(have {len(X)}); log more calls or label leads Good/Poor")
        torch.manual_seed(0)  # same data -> same model every time
        names = sorted(X[0])

        # Lists of dicts -> tensors. A tensor is PyTorch's array; float32 is what nn.Linear expects.
        xs = torch.tensor([[row[n] for n in names] for row in X], dtype=torch.float32)
        ys = torch.tensor(y, dtype=torch.float32)
        ws = torch.tensor(w, dtype=torch.float32)

        # Hold out whole leads (not single calls) so the check isn't fooled by calls from the same lead.
        groups = torch.tensor(lead_ids if lead_ids else range(len(X)))
        val = groups % VALIDATION_EVERY == 0
        if val.all() or not val.any() or len(set(ys[~val].tolist())) < 2:
            val = torch.zeros(len(X), dtype=torch.bool)

        net = LeadNet(len(names))
        opt = torch.optim.Adam(net.parameters(), lr=LEARNING_RATE, weight_decay=WEIGHT_DECAY)
        loss_fn = nn.BCEWithLogitsLoss(reduction="none")  # binary cross-entropy, one loss per example

        for _ in range(EPOCHS):
            opt.zero_grad()                                   # 1. clear old gradients
            logits = net(xs[~val])                            # 2. forward pass
            loss = (loss_fn(logits, ys[~val]) * ws[~val]).sum() / ws[~val].sum()  # 3. weighted loss
            loss.backward()                                   # 4. backprop: compute gradients
            opt.step()                                        # 5. nudge weights downhill

        metrics = {"examples": len(X), "positive_rate": round(ys.mean().item(), 3),
                   "train_loss": round(loss.item(), 4), "hidden": HIDDEN}
        if val.any():
            with torch.no_grad():  # no gradients needed when only evaluating
                p = torch.sigmoid(net(xs[val]))
            base = ys[~val].mean()
            metrics["val_examples"] = int(val.sum())
            metrics["val_brier_model"] = round(((p - ys[val]) ** 2).mean().item(), 4)
            metrics["val_brier_baseline"] = round(((base - ys[val]) ** 2).mean().item(), 4)
            metrics["beats_baseline"] = metrics["val_brier_model"] < metrics["val_brier_baseline"]
        return cls(net, names, metrics)

    def predict(self, rows):
        """Returns (probability, reasons) per row. Reasons = top features pushing the score up or down."""
        if not rows:
            return []
        xs = torch.tensor([[row.get(n, 0.0) for n in self.names] for row in rows], dtype=torch.float32)
        with torch.no_grad():
            probs = torch.sigmoid(self.net(xs)).tolist()
        if not isinstance(self.net.net, nn.Linear):  # MLP weights don't map to single features
            return [(round(p, 3), []) for p in probs]
        weights = self.net.net.weight[0]
        out = []
        for x, p in zip(xs, probs):
            contrib = (x * weights).tolist()  # weight x value = this feature's push on the score
            top = sorted(((c, n) for c, n in zip(contrib, self.names) if abs(c) > 0.05), key=lambda t: -abs(t[0]))[:3]
            out.append((round(p, 3), [f"{'+' if c > 0 else '-'} {n.replace('_', ' ')}" for c, n in top]))
        return out

    def save(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        torch.save({"state": self.net.state_dict(), "names": self.names, "metrics": self.metrics,
                    "hidden": HIDDEN}, path)

    @classmethod
    def load(cls, path):
        saved = torch.load(path, weights_only=True)
        net = LeadNet(len(saved["names"]), saved["hidden"])
        net.load_state_dict(saved["state"])
        net.eval()
        return cls(net, saved["names"], saved["metrics"])
