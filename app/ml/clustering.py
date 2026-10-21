"""K-Means behavioural clustering pipeline, model selection, profiling, and stability analysis.

Implements scikit-learn based clustering with standard scaling, cluster evaluation
(inertia, silhouette, Davies-Bouldin), inverse-scaled profiling, and permutation-invariant
stability audits using Adjusted Rand Index.
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
from typing import Any, Optional
import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler

# Headless matplotlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


@dataclass
class ClusterModelSelectionResult:
    """Evaluation metrics for a candidate k."""

    k: int
    inertia: float
    silhouette: float
    davies_bouldin: float
    calinski_harabasz: float
    cluster_sizes: list[int]
    cluster_proportions: list[float]
    min_cluster_size: int
    min_cluster_prop: float


class BehavioralKMeansPipeline:
    """Reproducible K-Means clustering pipeline with scaling and unscaled profiling."""

    def __init__(
        self,
        n_clusters: int = 3,
        random_state: int = 42,
        n_init: int = 10,
        max_iter: int = 300,
    ):
        if n_clusters < 2:
            raise ValueError(f"n_clusters must be at least 2; got {n_clusters}")

        self.n_clusters = n_clusters
        self.random_state = random_state
        self.n_init = n_init
        self.max_iter = max_iter

        self.scaler = StandardScaler()
        self.kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=self.n_init,
            max_iter=self.max_iter,
        )

        self.fitted_: bool = False
        self.feature_names_: list[str] = []
        self.cluster_centers_scaled_: Optional[np.ndarray] = None
        self.cluster_centers_unscaled_: Optional[pd.DataFrame] = None
        self.inertia_: float = 0.0
        self.silhouette_score_: float = 0.0
        self.davies_bouldin_score_: float = 0.0
        self.calinski_harabasz_score_: float = 0.0

    def fit(self, X: pd.DataFrame) -> "BehavioralKMeansPipeline":
        """Fit scaler and KMeans model on numerical feature matrix X."""
        if len(X) < self.n_clusters:
            raise ValueError(
                f"Sample size ({len(X)}) must be greater than or equal to n_clusters ({self.n_clusters})."
            )

        self.feature_names_ = list(X.columns)
        X_scaled = self.scaler.fit_transform(X)
        self.kmeans.fit(X_scaled)

        self.cluster_centers_scaled_ = self.kmeans.cluster_centers_
        # Inverse transform cluster centers back to original physical/behavioural units
        unscaled_centers = self.scaler.inverse_transform(self.cluster_centers_scaled_)
        self.cluster_centers_unscaled_ = pd.DataFrame(
            unscaled_centers,
            columns=self.feature_names_,
            index=[f"Cluster_{i}" for i in range(self.n_clusters)],
        )

        self.inertia_ = float(self.kmeans.inertia_)
        labels = self.kmeans.labels_

        # Calculate metrics when mathematically valid
        unique_labels = np.unique(labels)
        if len(unique_labels) > 1 and len(unique_labels) < len(X):
            self.silhouette_score_ = float(silhouette_score(X_scaled, labels))
            self.davies_bouldin_score_ = float(davies_bouldin_score(X_scaled, labels))
            self.calinski_harabasz_score_ = float(calinski_harabasz_score(X_scaled, labels))
        else:
            self.silhouette_score_ = float("nan")
            self.davies_bouldin_score_ = float("nan")
            self.calinski_harabasz_score_ = float("nan")

        self.fitted_ = True
        return self

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Predict cluster labels for input X."""
        if not self.fitted_:
            raise RuntimeError("Pipeline must be fitted before predict().")
        if list(X.columns) != self.feature_names_:
            raise ValueError(
                f"Feature columns mismatch. Expected: {self.feature_names_}, got: {list(X.columns)}"
            )

        X_scaled = self.scaler.transform(X)
        return self.kmeans.predict(X_scaled)

    def fit_predict(self, X: pd.DataFrame) -> np.ndarray:
        """Fit and predict cluster labels in one step."""
        return self.fit(X).predict(X)

    def compute_cluster_profiles(
        self,
        X_unscaled: pd.DataFrame,
        labels: Optional[np.ndarray] = None,
    ) -> pd.DataFrame:
        """Compute interpretable summary statistics in original feature units for each cluster."""
        if not self.fitted_:
            raise RuntimeError("Pipeline must be fitted before computing profiles.")

        if labels is None:
            labels = self.kmeans.labels_

        df_prof = X_unscaled[self.feature_names_].copy()
        df_prof["cluster"] = [f"Cluster_{lbl}" for lbl in labels]

        profiles = []
        total_samples = len(df_prof)

        for cluster_id, grp in df_prof.groupby("cluster"):
            cluster_size = len(grp)
            cluster_prop = round((cluster_size / total_samples) * 100.0, 2)

            row: dict[str, Any] = {
                "cluster": cluster_id,
                "size": cluster_size,
                "percentage": cluster_prop,
            }

            for col in self.feature_names_:
                row[f"{col}_mean"] = round(float(grp[col].mean()), 3)
                row[f"{col}_median"] = round(float(grp[col].median()), 3)
                row[f"{col}_std"] = round(float(grp[col].std()), 3) if len(grp) > 1 else 0.0

            profiles.append(row)

        return pd.DataFrame(profiles).sort_values("cluster").reset_index(drop=True)

    def save(self, output_path: str | Path) -> Path:
        """Serialize pipeline to a joblib file."""
        if not self.fitted_:
            raise RuntimeError("Cannot save an unfitted clustering pipeline.")

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        joblib.dump(self, path)
        return path

    @classmethod
    def load(cls, input_path: str | Path) -> "BehavioralKMeansPipeline":
        """Deserialize pipeline from a joblib file."""
        path = Path(input_path)
        if not path.exists():
            raise FileNotFoundError(f"Pipeline file not found: {path}")
        loaded = joblib.load(path)
        if not isinstance(loaded, cls):
            raise TypeError(f"Loaded object is not an instance of {cls.__name__}")
        return loaded


def evaluate_candidate_k(
    X: pd.DataFrame,
    k_range: range = range(2, 9),
    random_state: int = 42,
    output_dir: Optional[str | Path] = None,
    prefix: str = "daily",
) -> dict[str, Any]:
    """Evaluate candidate cluster counts k using inertia, silhouette, and size balance.

    Generates elbow curve, silhouette score curve, cluster sizes, and PCA visualizations.
    """
    if len(X) < max(k_range):
        raise ValueError(f"Sample size ({len(X)}) is smaller than max k ({max(k_range)})")

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    evaluations: list[ClusterModelSelectionResult] = []

    for k in k_range:
        km = KMeans(n_clusters=k, random_state=random_state, n_init=10)
        labels = km.fit_predict(X_scaled)
        inertia = float(km.inertia_)

        unique_labels, counts = np.unique(labels, return_counts=True)
        proportions = [round(float(c / len(X)) * 100.0, 2) for c in counts]

        sil = float(silhouette_score(X_scaled, labels)) if len(unique_labels) > 1 else 0.0
        db = float(davies_bouldin_score(X_scaled, labels)) if len(unique_labels) > 1 else 0.0
        ch = float(calinski_harabasz_score(X_scaled, labels)) if len(unique_labels) > 1 else 0.0

        evaluations.append(
            ClusterModelSelectionResult(
                k=k,
                inertia=round(inertia, 2),
                silhouette=round(sil, 4),
                davies_bouldin=round(db, 4),
                calinski_harabasz=round(ch, 2),
                cluster_sizes=[int(c) for c in counts],
                cluster_proportions=proportions,
                min_cluster_size=int(min(counts)),
                min_cluster_prop=round(float(min(proportions)), 2),
            )
        )

    # Visualization Generation
    plot_paths: list[str] = []
    if output_dir is not None:
        out_p = Path(output_dir)
        out_p.mkdir(parents=True, exist_ok=True)

        ks = [e.k for e in evaluations]
        inertias = [e.inertia for e in evaluations]
        silhouettes = [e.silhouette for e in evaluations]

        # 1. Elbow and Silhouette Joint Plot
        fig, ax1 = plt.subplots(figsize=(8, 5))
        color = "#2b5c8f"
        ax1.set_xlabel("Number of Clusters (k)", fontsize=11, fontweight="bold")
        ax1.set_ylabel("Inertia (Within-Cluster Sum of Squares)", color=color, fontsize=11)
        ax1.plot(ks, inertias, marker="o", color=color, linewidth=2, label="Inertia")
        ax1.tick_params(axis="y", labelcolor=color)
        ax1.grid(True, linestyle="--", alpha=0.5)

        ax2 = ax1.twinx()
        color = "#d95f02"
        ax2.set_ylabel("Silhouette Score", color=color, fontsize=11)
        ax2.plot(ks, silhouettes, marker="s", color=color, linewidth=2, linestyle="--", label="Silhouette")
        ax2.tick_params(axis="y", labelcolor=color)

        plt.title(f"K-Means Model Selection — Elbow & Silhouette ({prefix.replace('_', ' ').title()})", fontsize=12, fontweight="bold", pad=12)
        plt.tight_layout()
        elbow_path = out_p / f"{prefix}_elbow_and_silhouette.png"
        plt.savefig(elbow_path, dpi=200)
        plt.close()
        plot_paths.append(str(elbow_path))

        # 2. PCA 2D Cluster Projections for candidate models (k=2 and k=3)
        pca = PCA(n_components=2, random_state=random_state)
        X_pca = pca.fit_transform(X_scaled)
        var_exp = pca.explained_variance_ratio_

        for cand_k in [2, 3]:
            if cand_k in ks:
                km_cand = KMeans(n_clusters=cand_k, random_state=random_state, n_init=10)
                cand_labels = km_cand.fit_predict(X_scaled)

                plt.figure(figsize=(9, 6))
                scatter = plt.scatter(
                    X_pca[:, 0],
                    X_pca[:, 1],
                    c=cand_labels,
                    cmap="viridis",
                    alpha=0.6,
                    edgecolors="none",
                    s=25,
                )
                plt.colorbar(scatter, label="Cluster Label")
                plt.title(
                    f"PCA 2D Projection of Clusters (k={cand_k}, {prefix.replace('_', ' ').title()})\n"
                    f"PC1: {var_exp[0]*100:.1f}% var, PC2: {var_exp[1]*100:.1f}% var (Total: {sum(var_exp)*100:.1f}%)",
                    fontsize=11,
                    fontweight="bold",
                )
                plt.xlabel(f"Principal Component 1 ({var_exp[0]*100:.1f}% Variance)")
                plt.ylabel(f"Principal Component 2 ({var_exp[1]*100:.1f}% Variance)")
                plt.grid(True, linestyle="--", alpha=0.5)
                plt.tight_layout()
                pca_path = out_p / f"{prefix}_pca_clusters_k{cand_k}.png"
                plt.savefig(pca_path, dpi=200)
                plt.close()
                plot_paths.append(str(pca_path))

    return {
        "k_evaluations": [asdict(e) for e in evaluations],
        "plots": plot_paths,
    }


def evaluate_clustering_stability(
    X: pd.DataFrame,
    n_clusters: int = 3,
    seeds: Optional[list[int]] = None,
) -> dict[str, Any]:
    """Assess K-Means cluster assignment stability across random seeds via Adjusted Rand Index (ARI)."""
    if seeds is None:
        seeds = [42, 101, 202, 303, 404]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    label_runs = []
    inertias = []

    for seed in seeds:
        km = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
        labels = km.fit_predict(X_scaled)
        label_runs.append(labels)
        inertias.append(float(km.inertia_))

    # Calculate pairwise Adjusted Rand Index
    pairwise_aris = []
    n_runs = len(label_runs)
    for i in range(n_runs):
        for j in range(i + 1, n_runs):
            ari = float(adjusted_rand_score(label_runs[i], label_runs[j]))
            pairwise_aris.append(round(ari, 4))

    mean_ari = round(float(np.mean(pairwise_aris)), 4) if pairwise_aris else 1.0
    min_ari = round(float(np.min(pairwise_aris)), 4) if pairwise_aris else 1.0

    return {
        "n_clusters": n_clusters,
        "evaluated_seeds": seeds,
        "mean_adjusted_rand_index": mean_ari,
        "min_adjusted_rand_index": min_ari,
        "pairwise_aris": pairwise_aris,
        "inertia_mean": round(float(np.mean(inertias)), 2),
        "inertia_std": round(float(np.std(inertias)), 2),
        "stability_verdict": "High Stability" if mean_ari > 0.85 else ("Moderate Stability" if mean_ari > 0.65 else "Low Stability"),
    }
