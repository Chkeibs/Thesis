import numpy as np
import pandas as pd
from scipy.stats import norm
import os
import random

# Version equivalent to Version 3 22/04/2025
# Converted from Gauss to Python

def load_data():
    # --- 1. Chargement des données ---
    # Adaptez le chemin si besoin. On suppose un fichier texte séparé par des espaces.
    input_paths = [
        "/Users/thierrykamionka/Desktop/Chkeiban/Data_2026/Simulations/don11022026.txt",
        "./don11022026.txt"
    ]
    
    input_file = None
    for p in input_paths:
        if os.path.exists(p):
            input_file = p
            break
            
    if not input_file:
        raise FileNotFoundError("Fichier d'entrée non trouvé.")

    print(f"Lecture de {input_file}...")
    # Lecture en DataFrame d'abord pour gérer les types
    # low_memory=False évite le warning de type mixte, mais on convertit après
    df = pd.read_csv(input_file, sep=r'\s+', header=None, low_memory=False)

    # Conversion forcée en numérique (les chaines ou erreurs deviennent NaN)
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Equivalent de missrv(dvf, -999) : remplace -999 par NaN partout
    df = df.replace(-999, np.nan)

    dvf = df.values

    # Gestion du Reshape (si le fichier est lu comme un long vecteur par Gauss)
    if dvf.shape[1] == 1:
        dvf = dvf.reshape(-1, 41) # 38 au depart
    
    # Gauss: dvf = selif(dvf,(dvf[.,38] .ne -999))
    # Après missrv, -999 devient NaN ; on conserve les obs avec CP non manquant
    mask = ~np.isnan(dvf[:, 37])
    dvf = dvf[mask]
    
    
     # On Enlève les observations avec un code département erroné
    aux = dvf[:, 37] - 75000
    dvf = dvf[aux >= 1]

    n_obs = len(dvf)
    print(f"Nombre d'obs effectives: {n_obs}")
   

    # --- 2. Définition des Variables ---
    # Attention: Python commence à 0, Gauss à 1.
    Lprix = dvf[:, 0]
    nbp2 = dvf[:, 1]
    nbp3 = dvf[:, 2]
    nbp4 = dvf[:, 3]
    nbp5 = dvf[:, 4]
    surface = dvf[:, 5]
    Lsurface = dvf[:, 6]
    code_postal = dvf[:, 37] - 75000

    # Vérification stricte (équivalent GAUSS: on suppose 1..20)
    invalid_cp = np.isnan(code_postal) | (code_postal < 1) | (code_postal > 20)
    if np.any(invalid_cp):
        raise ValueError(
            f"Codes postaux hors 75001-75020: {int(np.sum(invalid_cp))} occurrences "
            f"(min={np.nanmin(code_postal)}, max={np.nanmax(code_postal)})"
        )

    code_postal = code_postal.astype(int)
    
    An = dvf[:, 36]
    An19 = (An == 2019).astype(float)
    An20 = (An == 2020).astype(float)
    An21 = (An == 2021).astype(float)
    An22 = (An == 2022).astype(float)
    An23 = (An == 2023).astype(float)
    An24 = (An == 2024).astype(float)
    
    Dependance = dvf[:, 8]
    D_center = dvf[:, 26]
    D_high = dvf[:, 24]
    D_best_high = dvf[:, 25]
    D_gare = dvf[:, 7]
    D_gare_200 = (D_gare <= 0.0200).astype(float)
    D_gare_300 = (D_gare >= 0.0300).astype(float)
    
    T0 = dvf[:, 9]; T1 = dvf[:, 10]
    Nb_Corresp2 = dvf[:, 11]; Nb_Corresp3 = dvf[:, 12]; Nb_Corresp4p = dvf[:, 13]
    
    G345 = dvf[:, 16] + dvf[:, 17] + dvf[:, 18]
    G6p = np.sum(dvf[:, 19:24], axis=1) # Somme colonnes 20 à 24 (Gauss) -> 19 à 23 (Python)
    Crime_fort = np.sum(dvf[:, 33:36], axis=1)
    Mean_Surface = dvf[:, 39]
    Mean_Pieces = dvf[:, 40]

    # Matrice X (Variables explicatives)
    X = np.column_stack((
        An19, An20, An21, An22, An23, An24,
        nbp2, nbp3, nbp4, nbp5,
        surface, Lsurface,
        Dependance,
        D_center, D_high, D_best_high,
        D_gare_200, D_gare_300,
        T0, T1,
        Nb_Corresp2, Nb_Corresp3, Nb_Corresp4p,
        G345, G6p, Crime_fort, Mean_Surface, Mean_Pieces
    ))
    
    names_var = [
                           "An19", "An20", "An21", "An22", "An23", "An24",
                           "nbp2", "nbp3", "nbp4", "nbp5",
                           "surface", "Lsurface",
                           "Dependance",
                           "D_center", "D_high", "D_best_high",
                            "D_gare_200", "D_gare_300",
                            "T0", "T1",
                            "Nb_Corresp2", "Nb_Corresp3", "Nb_Corresp4p",
                            "G345", "G6p", "Crime_fort", "Mean_Surface", "Mean_Pieces"
                          ]
    
    return Lprix, X, code_postal, n_obs, names_var


#def run_em(Lprix, X, code_postal, NbK=2, NbSimu=100, steps=200):

def run_em(Lprix, X, code_postal, NbK):
    nb_var = X.shape[1]
    n_obs = len(Lprix)
    NbSimu = 10000    # 100
    steps = 1000          # 200

    # --- 3. Simulation (Equivalent sans duplication) ---
    # Dans GAUSS, A = X .*. Un et Y = Lprix .*. Un répliquent les lignes NbSimu fois.
    # On évite la duplication mémoire en utilisant des comptages de tirages.

    # --- 4. Initialisation Paramètres ---
    b = np.zeros(nb_var)
    # Valeurs initiales du fichier Gauss
    b[0] = 0.034022920; b[1] = 0.059412169; b[2] = 0.070903060; 
    b[3] = 0.073894265; b[4] = 0.0013459450; b[5] = 0.0013459450;
    b[6] = 0.90615257 # Index 6 = nbp2 (Attention au mapping exact)
    
    g = np.array([9.3515343, 9.6632016]) # Intercepts des classes
    if NbK > len(g):
        # 2026-02-06: K>2 -> complete g avec intercepts aleatoires [9,10]
        extra = np.random.uniform(9.0, 10.0, size=NbK - len(g))
        g = np.concatenate([g, extra])
    sig2 = 0.12346260
            
    # Matrice de probabilités a priori (d) : 20 arrondissements x 2 classes
    d = np.ones((20, NbK)) / NbK 

    # --- 5. Boucle EM ---
    print("Debut de la boucle EM", steps, "étapes...")
    
    import time
    XTX = X.T @ X
    XTY = X.T @ Lprix

    for etape in range(1, steps + 1):
        step_start = time.time()
        
        # --- E-Step (Espérance) ---
        xb = X @ b
        # 2026-02-06: K=2 conserve la binomiale d'origine
        if NbK == 2:
            arg1 = Lprix - xb - g[0]
            arg2 = Lprix - xb - g[1]
            lik1 = norm.pdf(arg1, 0, np.sqrt(sig2))
            lik2 = norm.pdf(arg2, 0, np.sqrt(sig2))

            prior1 = d[code_postal - 1, 0]
            prior2 = d[code_postal - 1, 1]

            num1 = prior1 * lik1
            num2 = prior2 * lik2
            denom = num1 + num2
            denom[denom == 0] = 1e-12
            p1 = num1 / denom
            
            # --- Stochastic Step (Equivalent GAUSS) ---
            # NbSimu tirages par obs; pour NbK=2, c1 ~ Binomial(NbSimu, p1)
            c1 = np.random.binomial(NbSimu, p1)
            c2 = NbSimu - c1
            C = np.column_stack((c1, c2))
        else:
            # 2026-02-06: K>2 -> posterior par classe + tirage multinomial
            lik = np.empty((n_obs, NbK))
            for k in range(NbK):
                argk = Lprix - xb - g[k]
                lik[:, k] = norm.pdf(argk, 0, np.sqrt(sig2))

            prior = d[code_postal - 1, :]
            num = prior * lik
            denom = num.sum(axis=1, keepdims=True)
            denom[denom == 0] = 1e-12
            p = num / denom

            # --- Stochastic Step (general K) ---
            C = np.vstack([
                np.random.multinomial(NbSimu, p[i]) for i in range(n_obs)
            ])
        
        # --- M-Step (Maximisation) ---
        # Régression OLS via équations normales sans duplication
        XtX = np.zeros((nb_var + NbK, nb_var + NbK))
        XtY = np.zeros(nb_var + NbK)

        # Bloc X'X et X'Y pondérés par NbSimu
        XtX[:nb_var, :nb_var] = NbSimu * XTX
        XtY[:nb_var] = NbSimu * XTY

        # Blocs croisés X'Z et Z'X
        XTC = X.T @ C
        XtX[:nb_var, nb_var:] = XTC
        XtX[nb_var:, :nb_var] = XTC.T

        # Bloc Z'Z (diagonale des comptes)
        XtX[nb_var:, nb_var:] = np.diag(C.sum(axis=0))

        # Bloc Z'Y
        XtY[nb_var:] = C.T @ Lprix

        alp = np.linalg.solve(XtX, XtY)

        # Mise à jour des paramètres
        b = alp[:nb_var]
        g = alp[nb_var:]

        # Mise à jour Variance (Mean Squared Error)
        # 2026-02-06: K=2 conserve le calcul de variance d'origine
        if NbK == 2:
            resid1 = Lprix - (X @ b) - g[0]
            resid2 = Lprix - (X @ b) - g[1]
            sig2 = (c1 * resid1**2 + c2 * resid2**2).sum() / (len(Lprix) * NbSimu)
        else:
            # 2026-02-06: K>2 -> variance calculee sur toutes les classes
            resid = np.empty((n_obs, NbK))
            for k in range(NbK):
                resid[:, k] = Lprix - (X @ b) - g[k]
            sig2 = (C * resid**2).sum() / (len(Lprix) * NbSimu)
        
        # --- Mise à jour des Priors (d) ---
        # Fréquence empirique des classes par code postal
        for cp in range(1, 21):
            mask_cp = (code_postal == cp)
            if np.sum(mask_cp) > 0:
                counts_cp = C[mask_cp].sum(axis=0)
                d[cp-1, :] = counts_cp / (NbSimu * np.sum(mask_cp))
        
        if etape % 10 == 0:
            print(f"Etape {etape}: Sig2 = {sig2:.6f}") 

    return b, g, sig2, d, NbSimu, steps


# En principe ce qui suit ne sert plus � rien dans la mesure o� on ne compile pas ce programme directement

def main():
    Lprix, X, code_postal, n_obs = load_data()
    NbK = 2 # 2 Classes latentes
    b, g, sig2, d = run_em(Lprix, X, code_postal, NbK)

    print("\nMatrice finale des probabilités (d):")
    print(d)

    # Sauvegarde des résultats
    output_path = "resultats_lille.txt"
    
    with open(output_path, "w") as f:
        # 2026-02-06: sortie generalisee pour K>2
        f.write(f"Resultats Algorithme EM Lille K={NbK}\n")
        f.write(f"Nombre d'observations: {n_obs}\n")
        f.write(f"Sigma2 Final: {sig2}\n\n")
        f.write("Matrice des probabilités a posteriori par arrondissement (d):\n")
        # Formatage propre de la matrice
        # 2026-02-06: affiche toutes les classes pour chaque arrondissement
        for i in range(20):
            parts = [f"Class {k+1} = {d[i, k]:.4f}" for k in range(NbK)]
            f.write(f"Arrondissement {i+1}: " + ", ".join(parts) + "\n")
        
        f.write("\nCoefficients de regression (b):\n")
        for i, val in enumerate(b):
            f.write(f"Var {i}: {val}\n")
            
        # 2026-02-06: affiche toutes les constantes de classes
        f.write("\nConstantes de classes (g):\n")
        for k in range(NbK):
            f.write(f"Class {k+1}: {g[k]}\n")
        
    print(f"\nRésultats sauvegardés dans {output_path}")

if __name__ == "__main__":
    main()

