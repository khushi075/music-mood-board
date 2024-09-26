import os
import requests
from flask import Blueprint, request, redirect, url_for, session, render_template
from moodBoard.spotify_api.spotify_client import SpotifyClient
from moodBoard.spotify_api.spotify_handler import SpotifyHandler

auth_blueprint = Blueprint('auth_bp', __name__)

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')

spotify_client = SpotifyClient(client_id, client_secret, port=8002)
spotify_handler = SpotifyHandler()

@auth_blueprint.route("/")
def index():
    return 'belloe'

@auth_blueprint.route("/login", methods=['POST', 'GET'])
def login():
    """
    redirect to Spotify's log in page
    """
    auth_url = spotify_client.get_auth_url()
    return redirect(auth_url)


@auth_blueprint.route("/callback")
def callback():
    """
    set the session's authorization header
    """
    auth_token = request.args['code']
    spotify_client.get_authorization(auth_token)
    authorization_header = spotify_client.authorization_header
    session['authorization_header'] = authorization_header
    return redirect(url_for("auth_bp.inptxt"))

@auth_blueprint.route("/inptxt", methods=['GET', 'POST'])
def inptxt():
    """
    Page to input text, and return playlist recommendations based on that input.
    """
    authorization_header = session['authorization_header']
    def extract_letters(string):
        return ''.join([letter for letter in string if not letter.isdigit()])
    if request.method == 'POST':
        # Get the user input from the form
        user_input = request.form['user_input']
        
        # Call a function to get playlist recommendations based on input
        playlists = recommend_playlists(user_input)

        # Render a page showing the recommended playlists
        return render_template('recommendations.html', playlists=playlists)
    
    if request.method == 'GET':
        # -------- Get user's name, id, and set session --------
        profile_data = spotify_handler.get_user_profile_data(authorization_header)
        user_display_name, user_id = profile_data['display_name'], profile_data['id']
        session['user_id'], session['user_display_name'] = user_id, user_display_name

        # -------- Get user playlist data --------
        playlist_data = spotify_handler.get_user_playlist_data(authorization_header, user_id)
    
    # Render the form for user input
    return render_template('input_txt.html',user_display_name=user_display_name,
                               playlists_data=playlist_data,
                               func=extract_letters)

def recommend_playlists(text_input):
    """
    Function to recommend tracks based on user input using Spotify's recommendations API.
    The text input is analyzed to generate seed_genres, seed_artists, or seed_tracks.
    """
    # Sample mapping of moods/genres to Spotify seed genres or artists (this can be expanded)
    genre_map = {
    'happy': ['happy', 'dance', 'pop', 'funk'],
    'sad': ['sad', 'blues', 'rainy-day', 'emo', 'acoustic'],
    'calm': ['chill', 'ambient', 'acoustic', 'classical', 'folk', 'study'],
    'energetic': ['edm', 'party', 'club', 'dance', 'work-out', 'house'],
    'love': ['romance', 'latin', 'bossanova', 'soul', 'r-n-b'],
    'angry': ['hard-rock', 'heavy-metal', 'punk', 'grunge', 'metalcore'],
    'nostalgic': ['singer-songwriter', 'indie', 'folk', 'blues'],
    'dark': ['goth', 'industrial', 'black-metal', 'trip-hop'],
    'adventurous': ['world-music', 'reggae', 'indie-pop', 'alt-rock'],
    'romantic': ['romance', 'soul', 'latin', 'r-n-b'],
    'dreamy': ['ambient', 'new-age', 'piano', 'classical', 'soundtracks'],
    'groovy': ['funk', 'disco', 'groove', 'electro', 'dance'],
    'party': ['party', 'club', 'dance', 'edm', 'disco'],
    'relaxed': ['chill', 'ambient', 'acoustic', 'folk', 'study']
}
   # Analyze the text input and pick relevant seeds (for simplicity, let's focus on genres)
    seeds = []
    for word in text_input.lower().split():
        if word in genre_map:
            seeds.extend(genre_map[word])  # Flatten the list

    # Use a default genre if none were found in the input
    if not seeds:
        seeds = ['pop']  # Default genre if no specific match
    
     # Prepare parameters for the Spotify recommendations API
    params = {
        'limit': 10,  # Number of tracks to return
        'seed_genres': ','.join(seeds),  # Join the genres as a comma-separated string
        # Additional tunable parameters can be added here, such as 'energy', 'danceability', etc.
    }


    # Get the authorization header from the session
    authorization_header = session.get('authorization_header')
    
    # Make the request to Spotify's recommendations API
    recommendations_endpoint = 'https://api.spotify.com/v1/recommendations'
    response = requests.get(recommendations_endpoint, headers=authorization_header, params=params)
    
    # Parse the response
    recommendation_results = response.json()
    
    # Extract track data
    tracks = recommendation_results.get('tracks', [])
    # print(tracks[0])
    # Prepare track data for display
    track_data = []
    for track in tracks:
        track_data.append({
            'name': track['name'],
            'artist': track['artists'][0]['name'],
            'url': track['external_urls']['spotify'],
            'image': track['album']['images'][0]['url'] if track['album']['images'] else None,
            'uri': track['id']  # Add the Spotify URI for embedding
        })
    
    return track_data
