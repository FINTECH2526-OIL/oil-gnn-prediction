import numpy as np
from sklearn.decomposition import PCA
from scipy.sparse import csr_matrix
from scipy.sparse.linalg import eigsh
from tqdm import tqdm

class SimpleGraphFeatureExtractor:
    def __init__(self, n_components=16):
        self.n_components = n_components
        self.pca = None

    def create_adjacency_matrix(self, df_snapshot):
        unique_countries = df_snapshot['country_iso3'].unique()
        n_countries = len(unique_countries)
        country_to_idx = {c: i for i, c in enumerate(unique_countries)}

        adj_matrix = np.eye(n_countries, dtype=np.float32)

        opec_countries = ['SAU', 'IRQ', 'IRN', 'KWT', 'ARE', 'VEN', 'NGA', 'LBY', 'DZA', 'AGO']
        for i, c1 in enumerate(unique_countries):
            for j, c2 in enumerate(unique_countries):
                if c1 in opec_countries and c2 in opec_countries and i != j:
                    adj_matrix[i, j] = 0.8

        if 'goldstein' in df_snapshot.columns:
            for i in range(n_countries):
                for j in range(i+1, n_countries):
                    country_i_data = df_snapshot[df_snapshot['country_iso3'] == unique_countries[i]]
                    country_j_data = df_snapshot[df_snapshot['country_iso3'] == unique_countries[j]]

                    if len(country_i_data) > 0 and len(country_j_data) > 0:
                        goldstein_i = country_i_data['goldstein'].mean()
                        goldstein_j = country_j_data['goldstein'].mean()

                        if not np.isnan(goldstein_i) and not np.isnan(goldstein_j):
                            similarity = 1.0 / (1.0 + abs(goldstein_i - goldstein_j))
                            if similarity > 0.5:
                                adj_matrix[i, j] = max(adj_matrix[i, j], similarity)
                                adj_matrix[j, i] = max(adj_matrix[j, i], similarity)

        return adj_matrix, country_to_idx

    def extract_spectral_features(self, adj_matrix, node_features):
        n_nodes = adj_matrix.shape[0]
        n_features = node_features.shape[1] if len(node_features.shape) > 1 else 1

        if n_nodes < 3:
            return np.zeros((1, self.n_components))

        degree_matrix = np.diag(adj_matrix.sum(axis=1))
        laplacian = degree_matrix - adj_matrix

        try:
            if n_nodes > 3:
                laplacian_sparse = csr_matrix(laplacian)
                k = min(3, n_nodes - 1)
                eigenvalues, eigenvectors = eigsh(laplacian_sparse, k=k, which='SM')
                spectral_features = eigenvectors.T
            else:
                spectral_features = np.random.randn(1, n_nodes) * 0.01
        except:
            spectral_features = np.random.randn(1, n_nodes) * 0.01

        graph_features = []

        if n_features > 0:
            graph_features.append(np.mean(node_features, axis=0))
            graph_features.append(np.std(node_features, axis=0))
            graph_features.append(np.max(node_features, axis=0))
            graph_features.append(np.min(node_features, axis=0))

        for i in range(min(spectral_features.shape[0], 3)):
            if n_features > 0 and spectral_features.shape[1] == n_nodes:
                weighted_features = spectral_features[i].reshape(-1, 1) * node_features
                graph_features.append(np.mean(weighted_features, axis=0))

        if len(graph_features) > 0:
            combined_features = np.concatenate(graph_features)
        else:
            combined_features = np.zeros(self.n_components)

        final_dim = min(len(combined_features), self.n_components)
        if len(combined_features) > self.n_components:
            combined_features = combined_features[:self.n_components]
        elif len(combined_features) < self.n_components:
            padded = np.zeros(self.n_components)
            padded[:len(combined_features)] = combined_features
            combined_features = padded

        return combined_features.reshape(1, -1)

    def extract_graph_features(self, df_model, feature_cols):
        print("Extracting graph-based features...")

        dates = df_model['date'].unique()
        graph_features_dict = {}

        valid_dates = 0
        for date in tqdm(dates, desc="Processing dates"):
            date_data = df_model[df_model['date'] == date]

            if len(date_data['country_iso3'].unique()) < 2:
                continue

            adj_matrix, country_to_idx = self.create_adjacency_matrix(date_data)

            features_matrix = []
            for country in date_data['country_iso3'].unique():
                country_data_sub = date_data[date_data['country_iso3'] == country]
                selected_cols = list(set(feature_cols.array) & set(country_data_sub.columns))
                if len(country_data_sub) > 0:
                    features = country_data_sub[selected_cols].iloc[0].values
                    features_matrix.append(features)

            if len(features_matrix) > 0:
                features_matrix = np.array(features_matrix, dtype=np.float32)
                features_matrix = np.nan_to_num(features_matrix, nan=0.0)

                graph_embedding = self.extract_spectral_features(adj_matrix, features_matrix)
                graph_features_dict[date] = graph_embedding.flatten()
                valid_dates += 1

        print(f"Processed {valid_dates} valid dates out of {len(dates)} total dates")

        graph_feature_cols = [f'graph_feat_{i}' for i in range(self.n_components)]
        for col in graph_feature_cols:
            df_model[col] = 0.0

        for date, features in graph_features_dict.items():
            mask = df_model['date'] == date
            for i in range(min(len(features), len(graph_feature_cols))):
                df_model.loc[mask, graph_feature_cols[i]] = features[i]

        return df_model, graph_feature_cols

# graph_extractor = SimpleGraphFeatureExtractor(n_components=16)
# df_model_enhanced, graph_feature_cols = graph_extractor.extract_graph_features(df_model.copy(), feature_cols)

# print(f"Added {len(graph_feature_cols)} graph-based features")