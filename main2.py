# -*- coding: utf-8 -*-

import requests
import csv
import config
import os
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)
admin_username="admin"
admin_password = "123456789"

@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def process_login():
    username=request.form.get('username')
    user_password = request.form.get('admin_password')
    if user_password == admin_password and username==admin_username :
        return redirect(url_for('index'))
    else:
        return render_template('login.html', error='Invalid credentials')

@app.route('/index')
def index():
    return render_template('index.html')


@app.route('/search_and_save', methods=['POST'])
def search_and_save():
    # TMDb API URL
    api_url = "https://api.themoviedb.org/3/discover/movie"
    
    api_key = config.api_key
    
    num_movies = int(request.form.get('num_movies')) 
    release_year = request.form.get('release_year') 

    params = {
        'api_key': api_key,
        'language': 'en-US',
        'sort_by': 'popularity.desc',
        'include_adult': 'false',
        'include_video': 'false',
        'page': 1 , 
        'primary_release_year': release_year
    }
    selected_genre = request.form.get('genre')
    if selected_genre:
        params['with_genres'] = selected_genre
    
    movies_data = []
    num_pages = (num_movies + 19) // 20

    for page in range(1, (num_pages + 1)):
        params['page'] = page
        response = requests.get(api_url, params=params)
    
        if response.status_code == 200:
            movie_data = response.json().get('results')
            movies_data.extend(movie_data)
    csv_file = request.form.get('file_name')
    file_name = csv_file + '.csv'
    file_mode = request.form.get('file_mode')
    mode = 'a' if file_mode == 'append' else 'w'
    with open(file_name, mode, newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        writer.writerow(['Title', 'Release Date', 'Overview', 'Popularity', 'Vote Average', 'Vote Count', 'Keywords', 'Runtime', 'Cast', 'Director', 'Editor', 'Poster URL','ImdbId','Income','Genre'])
        
        for movie in movies_data:
            movie_details_url = f"https://api.themoviedb.org/3/movie/{movie['id']}"
            details_response = requests.get(movie_details_url, params={'api_key': api_key, 'append_to_response': 'credits,keywords'})
            details = details_response.json()
        
            keywords = ', '.join(keyword['name'] for keyword in details.get('keywords', {}).get('keywords', []))
        
            runtime = details.get('runtime', 'N/A')
        
            cast = ', '.join(member['name'] for member in details.get('credits', {}).get('cast', []))
        
            crew_url = f"https://api.themoviedb.org/3/movie/{movie['id']}/credits"
            crew_response = requests.get(crew_url, params={'api_key': api_key})
            crew = crew_response.json().get('crew', [])
        
            directors = ', '.join(member['name'] for member in crew if member['job'] == 'Director')
            
            editors = ', '.join(member['name'] for member in crew if member['job'] == 'Editor')

            poster_url = f"https://image.tmdb.org/t/p/original/{details.get('poster_path')}" if details.get('poster_path') else 'N/A'
            poster_folder = 'poster_images'
            if poster_url != 'N/A':
                imdb_id = movie['id']
                poster_filename = os.path.join(poster_folder, f'{imdb_id}.jpg')
                response = requests.get(poster_url)
                if response.status_code == 200:
                    with open(poster_filename, 'wb') as poster_file:
                        poster_file.write(response.content)
                else:
                    print("failed")
            else:
                poster_filename = 'N/A'
            
            income = details.get('revenue', 'N/A')
            
            genres = ', '.join(genre['name'] for genre in details.get('genres', []))
            
            writer.writerow([movie['title'], movie['release_date'], movie['overview'], movie['popularity'], movie['vote_average'], movie['vote_count'], keywords, runtime, cast, directors, editors, poster_url, imdb_id, income, genres])
    
    print(f'{len(movies_data)} movies data saved to {csv_file}2')
    return redirect(url_for('index'))
if __name__ == '__main__':
    app.run(debug=True, port=8080)
