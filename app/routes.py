import requests
from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__)
df = pd.read_csv('C:/Users/kvtts/OneDrive/Desktop/COURS/webscrapping/flask/app/result.csv', sep=',')
CARBON_INTERFACE_API_KEY = 'ZAVdjq8U5QKDMabJn6wChQ'

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/airports', methods=['GET'])
def airports():
    """
    Fournit une liste des villes d'aéroports uniques avec leurs codes IATA
    triée par ordre alphabétique.
    """
    airports = df[['start', 'start_iata']].drop_duplicates()
    airports.rename(columns={'start': 'city', 'start_iata': 'iata'}, inplace=True)
    # Trier par ordre alphabétique des villes
    airports = airports.sort_values(by='city')
    return jsonify(airports.to_dict(orient='records'))

@app.route('/search', methods=['POST'])
def search():
    """
    Recherche un vol selon la ville de départ et d'arrivée,
    calcule la moyenne des sentiments et retourne une note en étoiles.
    """
    departure = request.form.get('departure')
    arrival = request.form.get('arrival')

    # Filtrer selon les villes de départ et d'arrivée
    filtered_df = df[(df['start'] == departure) & (df['end'] == arrival)]
    
    if filtered_df.empty:
        return jsonify({'message': 'Aucun vol trouvé pour ce trajet.'})
    
    # Calculer la moyenne des sentiments
    sentiment_mean = filtered_df['sentiment'].mean()

    # Déterminer la note en étoiles
    if -1 <= sentiment_mean < -0.8:
        stars = 0
    elif -0.8 <= sentiment_mean < -0.4:
        stars = 1
    elif -0.4 <= sentiment_mean < 0:
        stars = 2
    elif 0 <= sentiment_mean < 0.4:
        stars = 3
    elif 0.4 <= sentiment_mean < 0.8:
        stars = 4
    elif 0.8 <= sentiment_mean <= 1:
        stars = 5
    else:
        stars = 0  # Par sécurité, en cas de valeur hors de l'intervalle attendu

    # Appeler l'API Carbon Interface pour obtenir les émissions de CO₂
    emissions = get_carbon_emissions(filtered_df['start_iata'].iloc[0], filtered_df['start_iata'].iloc[0])

    result = {
        'departure': departure,
        'arrival': arrival,
        'price': filtered_df['prix_final'].iloc[0],  # Afficher le prix du vol
        'stars': stars,
        'emissions': emissions
    }

    return jsonify(result)

def get_carbon_emissions(departure_iata, arrival_iata):
    """
    Utilise l'API Carbon Interface pour calculer les émissions de CO₂ pour un vol
    donné en utilisant les codes IATA de départ et d'arrivée.
    """
    url = 'https://api.carboninterface.com/v1/estimates'

    headers = {
        'Authorization': f'Bearer {CARBON_INTERFACE_API_KEY}',
        'Content-Type': 'application/json'
    }

    payload = {
        "flight": {
            "departure_airport_code": departure_iata,
            "arrival_airport_code": arrival_iata,
            "passenger_count": 1  
        }
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Cela déclenche une exception pour les erreurs HTTP

        emissions_data = response.json()
        # Vérifier si les données d'émissions sont présentes
        carbon_g = emissions_data.get('data', {}).get('carbon_kg', None)
        if carbon_g is not None:
            return carbon_g
        else:
            return 'Indisponible'  # Retourner "Indisponible" si la donnée est absente

    except requests.exceptions.RequestException as e:
        print(f"Error : {e}")
        return 'Indisponible'


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
