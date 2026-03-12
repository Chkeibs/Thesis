import numpy as np
from scipy.stats import norm

import os
os.chdir('/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Simulations')

from lille_K2_python_BIC import load_data, run_em

# BIC selection for K=2..12 using the Lille EM model

def compute_bic(Lprix, X, code_postal, b, g, sig2, d):
    n_obs = len(Lprix)
    NbK = len(g)
    nb_var = X.shape[1]

    xb = X @ b
    lik = np.empty((n_obs, NbK))
    for k in range(NbK):
        argk = Lprix - xb - g[k]
        lik[:, k] = norm.pdf(argk, 0, np.sqrt(sig2))

    prior = d[code_postal - 1, :]
    mix = (prior * lik).sum(axis=1)
    mix[mix == 0] = 1e-12
    loglik = np.log(mix).sum()

    # df = nb_var (b) + NbK (g) + 1 (sig2) + 20*(NbK-1) (d)
    bic_df = nb_var + NbK + 20 * (NbK - 1)
    bic = -2 * loglik + np.log(n_obs) * bic_df

    return bic


def main():
    Lprix, X, code_postal, n_obs, names_var = load_data()

    K_min = 2
    K_max = 15
    #results = []

    for k in range(K_min, K_max + 1):
        b, g, sig2, d, NbSimu, steps = run_em(Lprix, X, code_postal, k)
        bic = compute_bic(Lprix, X, code_postal, b, g, sig2, d)
        
        filename = f"/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Simulations/Resultats/resultats_lille_bicK={k}.txt"
        output_path = filename
        
        with open(output_path, "w") as f:
         f.write(f"Resultats Algorithme EM Lille K={k}\n")
         #print(f"BIC (K={k}): {bic:.6f}")
         f.write(f"BIC (K={k}): {bic:.6f}\n")
         f.write(f"Nombre d'observations: {n_obs}\n")
         f.write(f"Nombre de simulations: {NbSimu}\n")
         f.write(f"Nombre d'étapes: {steps}\n")
         f.write(f"Sigma2 Final: {sig2}\n\n")
         f.write("Matrice des probabilités a posteriori par arrondissement (d):\n")
         # Formatage propre de la matrice
         for i in range(20):
             parts = [f"Class {k+1} = {d[i, k]:.4f}" for k in range(k)]
             f.write(f"Arrondissement {i+1}: " + ", ".join(parts) + "\n")
         f.write("\nCoefficients de regression (b):\n")
         for i, val in enumerate(b):
            f.write(f"Var {i} {names_var[i]}: {val}\n")
            
         f.write("\nConstantes de classes (g):\n")
         for k in range(k):
             f.write(f"Class {k+1}: {g[k]}\n")
        
         print(f"\nRésultats sauvegardés dans {output_path}")

        
        
        
# Remarque : le nombre de simulation Nbsimu et le nombre d'étapes steps peuvent être modifiés dans le programme appelé:
# lille_K2_python_BIC

if __name__ == "__main__":
    main()
