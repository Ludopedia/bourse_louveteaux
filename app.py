from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import json

app = Flask(__name__)

# Chargement de la configuration
with open("config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

sizaines = config["sizaines"]  # Liste des sizaines
capitaux_initiaux = config["capitaux_initiaux"]  # Capitaux de départ par sizaine

# Chargement des prix prédéfinis des actions
df_evolution = pd.read_csv("bourse.csv")

der_tour = len(df_evolution) - 1  # Nombre total de tours disponibles
dernier_tour = 0  # Tour actuel
prix_actuels = df_evolution.iloc[dernier_tour, 1:].to_dict()

# Initialisation des portefeuilles
def init_portefeuilles():
    return {sizaine: {"liquidite": capitaux_initiaux.get(sizaine, 100), "actions": {action: 0 for action in prix_actuels.keys()}} for sizaine in sizaines}

portefeuilles = init_portefeuilles()

@app.route("/")
def index():
    all_tours = df_evolution["Tour"].tolist()
    historique_actions = {col: df_evolution[col].tolist() for col in df_evolution.columns if col != "Tour"}
    return render_template("index.html", prix_actuels=prix_actuels, dernier_tour=dernier_tour,
                           all_tours=all_tours, historique_actions=historique_actions, sizaines=sizaines)

def calculer_valeur_portefeuille(sizaine):
    portefeuille = portefeuilles[sizaine]
    valeur_actions = sum(portefeuille["actions"][action] * prix_actuels[action] for action in prix_actuels)
    portefeuille["valeur_totale"] = portefeuille["liquidite"] + valeur_actions

@app.route("/sizaine/<nom>")
def sizaine(nom):
    if nom not in portefeuilles:
        return "Sizaine inconnue", 404
    calculer_valeur_portefeuille(nom)
    return render_template("sizaine.html", sizaine=nom, portefeuille=portefeuilles[nom], prix_actuels=prix_actuels)

@app.route("/transaction", methods=["POST"])
def transaction():
    nom_sizaine = request.form["sizaine"]
    action = request.form["action"]
    quantite = int(request.form["quantite"])
    type_operation = request.form["type"]

    if nom_sizaine not in portefeuilles or action not in prix_actuels:
        return "Erreur dans la transaction", 400

    portefeuille = portefeuilles[nom_sizaine]
    prix = prix_actuels[action]

    if type_operation == "achat":
        cout_total = quantite * prix
        if portefeuille["liquidite"] >= cout_total:
            portefeuille["liquidite"] -= cout_total
            portefeuille["actions"][action] += quantite
        else:
            return "Fonds insuffisants", 400

    elif type_operation == "vente":
        if portefeuille["actions"][action] >= quantite:
            portefeuille["actions"][action] -= quantite
            portefeuille["liquidite"] += quantite * prix
        else:
            return "Pas assez d'actions à vendre", 400

    calculer_valeur_portefeuille(nom_sizaine)
    return redirect(url_for("sizaine", nom=nom_sizaine))

@app.route("/modifier_cash", methods=["POST"])
def modifier_cash():
    nom_sizaine = request.form["sizaine"]
    montant = int(request.form["montant"])
    type_operation = request.form["type"]

    if nom_sizaine not in portefeuilles:
        return "Sizaine inconnue", 400

    if type_operation == "ajouter":
        portefeuilles[nom_sizaine]["liquidite"] += montant
    elif type_operation == "retirer":
        if portefeuilles[nom_sizaine]["liquidite"] >= montant:
            portefeuilles[nom_sizaine]["liquidite"] -= montant
        else:
            return "Fonds insuffisants", 400

    calculer_valeur_portefeuille(nom_sizaine)
    return redirect(url_for("sizaine", nom=nom_sizaine))

@app.route("/next_round")
def next_round():
    global dernier_tour, prix_actuels
    if dernier_tour < der_tour:
        dernier_tour += 1
        prix_actuels = df_evolution.iloc[dernier_tour, 1:].to_dict()
    return redirect(url_for("index"))

@app.route("/previous_round")
def previous_round():
    global dernier_tour, prix_actuels
    if dernier_tour > 0:
        dernier_tour -= 1
        prix_actuels = df_evolution.iloc[dernier_tour, 1:].to_dict()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(debug=True)
