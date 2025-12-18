import numpy as np

def calculate_topsis(matrix, weights, criteria_types):
    matrix = np.array(matrix, dtype=float)
    weights = np.array(weights, dtype=float)

    # 1. Normalisasi
    norm = np.sqrt((matrix ** 2).sum(axis=0))
    normalized = matrix / norm

    # 2. Pembobotan
    weighted = normalized * weights

    # 3. Solusi Ideal
    ideal_pos = []
    ideal_neg = []

    for i, ctype in enumerate(criteria_types):
        if ctype == "benefit":
            ideal_pos.append(weighted[:, i].max())
            ideal_neg.append(weighted[:, i].min())
        else:  # cost
            ideal_pos.append(weighted[:, i].min())
            ideal_neg.append(weighted[:, i].max())

    ideal_pos = np.array(ideal_pos)
    ideal_neg = np.array(ideal_neg)

    # 4. Jarak
    d_pos = np.sqrt(((weighted - ideal_pos) ** 2).sum(axis=1))
    d_neg = np.sqrt(((weighted - ideal_neg) ** 2).sum(axis=1))

    # 5. Nilai Preferensi
    preference = d_neg / (d_pos + d_neg)

    # 6. Ranking
    ranking = preference.argsort()[::-1] + 1

    return ranking, preference
