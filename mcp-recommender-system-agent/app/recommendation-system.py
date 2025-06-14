# server.py
from mcp.server.fastmcp import FastMCP
import os
import json
import time
import ast
import traceback
import uuid
# Custom Modules
from utilities.google_sheet_utilities import GoogleSheetUtils
from utilities.similarity_search_utilities import SimilaritySearchUtilities
from utilities.train_model_utilties import train_movie_rating_model, predict_rating_of_movie

from Config import SERVICE_ACCOUNT_FILE_PATH, SPREADSHEET_ID, RANGE

SERVICE_ACCOUNT_FILE_PATH = SERVICE_ACCOUNT_FILE_PATH
SPREADSHEET_ID = SPREADSHEET_ID
RANGE = RANGE
SHEET_NAME = "movies_list"

# Create an MCP server
mcp = FastMCP("AI Recommendation System")

def row_to_json(row):
    row_dict = row.drop('Embeddings').to_dict()
    json_str = json.dumps(row_dict)
    return json_str
# Add an addition tool
print("Loading the Model for Similarity Search")
similarity_search_utilities = SimilaritySearchUtilities()
print("Loaded the Model for Similarity Search")

def get_similarity_search_utilities() -> str:
    return "Similarity Search Utilities"

def to_optional_float(val):
    return float(val) if val not in ("", None) else 0

def to_optional_int(val):
    return int(val) if val not in ("", None) else 0

# Tool Working
@mcp.tool()
def hello_world() -> str:
    """
    A simple hello world function that returns a greeting message.
    
    Returns:
        str: A greeting message "Hello from MCP tool!"
    """
    return "Hello from MCP tool!"

# Tool not Working TODO
@mcp.tool()
def generate_and_store_embeddings_for_docs() -> str:
    '''
    Call this tool when the user asks to generate embeddings for documents in Google Sheets and stores them.
    
    Returns:
        str: A message indicating how many documents were processed
    
    '''
    try:
        google_sheet_utilities = GoogleSheetUtils(SERVICE_ACCOUNT_FILE_PATH, SPREADSHEET_ID, SHEET_NAME)
        
        df = google_sheet_utilities.read_range(range_name = RANGE, as_dataframe = True)
        print(df.columns)
        print(df.shape)
        # Check if dataframe is empty
        if df.empty:
            return "No documents found"


        # # Only process rows that are missing embeddings or have empty ones
        df_to_embed = df[df['Embeddings'] == "-"]
        print(df_to_embed.shape)
        

        # if df_to_embed.empty:
        #     return "All documents already have embeddings"

        for _, row in df_to_embed.iterrows():
            try:
                row_json = row_to_json(row)
                # TODO: NEED TO REMOVE UNNECESSARY FIELDS FROM THE ROW JSON

                embedding = similarity_search_utilities.generate_embedding(row_json)
                # print("embedding: ", embedding)
                if embedding is not None and len(embedding) > 0:
                    embedding_list = embedding.tolist()
                    google_sheet_utilities.update_cell_by_id(
                        id_value=row['ID'],
                        target_column="Embeddings",
                        new_value=embedding_list
                    )
            except Exception as e:
                # Log the error or handle it accordingly
                print(f"Failed to process ID {row['ID']}: {e}")

        return f"Processed {len(df_to_embed)} documents and stored embeddings"
    except Exception as e:
        print(e)
        print(traceback.print_exc())
        return "Error: " + str(e) + "TRACEBACK: " + traceback.print_exc()

# Tool Working
@mcp.tool()
def get_details_of_movie(user_query: str) -> str:
    """
    Call this tool when the user asks for details about a movie.
    
    This function:
    1. Takes a user query about a movie
    2. Generates embeddings for the query
    3. Performs similarity search to find matching movies
    4. Returns movie details if found in database
    5. If not found, searches web and prompts to add to database
    
    Args:
        user_query (str): The user's movie search query or question
        
    Returns:
        str: Details about the requested movie or status message

    """
    try:
        # get all the embeddings from the sheets
        gsheet = GoogleSheetUtils(SERVICE_ACCOUNT_FILE_PATH, SPREADSHEET_ID, SHEET_NAME)
        df = gsheet.read_range(range_name = RANGE, as_dataframe = True)
        # Check if dataframe is empty
        if df.empty:
            return "No documents found"

        # get all the embeddings in a list
        df['Embeddings'] = df['Embeddings'].apply(lambda x: ast.literal_eval(x) if isinstance(x, str) else x)
        doc_embeddings_list = df['Embeddings'].tolist()
        # get all the documents rows in a list except the embeddings column
        doc_rows_list = df.drop('Embeddings', axis=1).to_dict(orient='records')

        user_query = user_query.lower()
        # print("user_query_embeddings: ", user_query_embeddings)

        # get the top 5 results
        top_5_results = similarity_search_utilities.get_top_k_results(user_query, doc_embeddings_list, doc_rows_list, top_k=5)

        prompt = f"Here are the top results generated by the similarity search: {top_5_results['top_k_documents']}. This is the User Query: {user_query}. Please check if the results are relevant to the user query and answer the user query. "

        # If not, then search the web for the details of the movie and return the details to the user. If the results are relevant, then return the details of the movie. If the user wants to add the details to the database, then prompt the user to add the details to the database. If the user wants to add the details to the database, then prompt the user to add the details to the database.
        return prompt
    except Exception as e:
        print(e)
        print(traceback.print_exc())
        return "Error: " + str(e) + "TRACEBACK: " + traceback.print_exc()

# Tool Working
@mcp.tool()
def train_the_model() -> str:
    """
    Call this tool when the user asks to train the model for recommending the movies.
    
    Returns:
        str: A message indicating how many documents were processed
    """
    try:
        gsheet = GoogleSheetUtils(SERVICE_ACCOUNT_FILE_PATH, SPREADSHEET_ID, SHEET_NAME)
        df = gsheet.read_range(range_name = RANGE, as_dataframe = True)
        # Check if dataframe is empty
        if df.empty:
            return "No documents found"
        
        train_movie_rating_model(data = df)
        return "Model trained successfully"
    except Exception as e:
        print(e)
        print(traceback.print_exc())
        return "Error: " + str(e) + "TRACEBACK: " + traceback.print_exc()

# Tool Working
@mcp.tool()
def rate_the_movie(movie_details_information) -> dict:
    """
    Use this tool when the user asks to:
    1. Rate a movie.
    2. Decide whether to watch a specific movie based on details.

    Processing Instructions:
    -------------------------------------------------------------------
    1. Start by extracting any available movie details from the user's input.
    2. If key information is missing, do the following:
        a. First, attempt to fetch the missing information by calling the tool `get_details_of_movie`.
        b. If the tool returns incomplete or empty data, then fetch missing details from the web (IMDb, Wikipedia, TMDb, etc.).
    3. Combine and update the data to form a **complete dictionary**.
       - Use only these keys (exact match):
         ['ID', 'Movie Name', 'Year', 'Timing(min)', 'Genre', 'Language',
          'Brief Description', 'Cast', 'Director', 'Screenplay/Writer',
          'Production Company', 'Budget in Rupees', 'Revenue in Rupees']
       - All keys must be present. If any data is unknown even after enrichment, set the value to an empty string.
    4. Once the dictionary is fully prepared, compulsorily pass it to the tool `provide_the_reviews_for_the_movie`.

    Args:
        movie_details_information (str): User-provided description or partial movie data.

    Returns:
        dict: A dictionary of formatted and enriched movie details.
    """
    try:
        return  """
    Use this tool when the user asks to:
    1. Rate a movie.
    2. Decide whether to watch a specific movie based on details.

    Processing Instructions:
    -------------------------------------------------------------------
    1. Start by extracting any available movie details from the user's input.
    2. If key information is missing, do the following:
        a. First, attempt to fetch the missing information by calling the tool `get_details_of_movie`.
        b. If the tool returns incomplete or empty data, then fetch missing details from the web (IMDb, Wikipedia, TMDb, etc.).
    3. Combine and update the data to form a **complete dictionary**.
       - Use only these keys (exact match):
         ['ID', 'Movie Name', 'Year', 'Timing(min)', 'Genre', 'Language',
          'Brief Description', 'Cast', 'Director', 'Screenplay/Writer',
          'Production Company', 'Budget in Rupees', 'Revenue in Rupees']
       - All keys must be present. If any data is unknown even after enrichment, set the value to an empty string.
    4. Once the dictionary is fully prepared, compulsorily pass it to the tool `provide_the_reviews_for_the_movie`.

    Args:
        movie_details_information (str): User-provided description or partial movie data.

    Returns:
        dict: A dictionary of formatted and enriched movie details.
        """
    except Exception as e:
        print(e)
        print(traceback.print_exc())
        return "Error: " + str(e) + "TRACEBACK: " + traceback.print_exc()

# Tool Working
@mcp.tool()
def provide_the_reviews_for_the_movie(movie_details) -> str:
    """
    Args:
        movie_details (dict): The details of the movie

    Returns:
        str: A message indicating how many documents were processed
    
    """
    try:
        predicted_rating = predict_rating_of_movie(movie_details)

        gsheet = GoogleSheetUtils(SERVICE_ACCOUNT_FILE_PATH, SPREADSHEET_ID, SHEET_NAME)
        df = gsheet.read_range(range_name = RANGE, as_dataframe = True)
        # Check if dataframe is empty
        if df.empty:
            return "No documents found"
        
        df['User Rating'] = df['User Rating'].astype(float)
        rounded_rating = round(predicted_rating, 2)
        filtered_df = df[(df['User Rating'] >= rounded_rating - 1) & (df['User Rating'] <= rounded_rating)]
        list_of_reviews_provided_by_user = filtered_df['User Liking (words)'].tolist()


        return f"""The user has not seen or rated the movie , but is considering watching it. A machine learning model has predicted that the user would rate this movie {predicted_rating} out of 10. 
        
        You are also given a list of past reviews by the same user for other movies that fall within a similar rating range (e.g., within ±0.5 of the predicted rating). for example: {list_of_reviews_provided_by_user}
        
        Based on this predicted rating and the user's review history of similar movies, determine whether the user is likely to enjoy the movie and whether they should watch it. Justify your answer clearly and briefly, referencing the users review patterns. Do not generate a generic movie review. This is a personalized recommendation, not a film critique."""
    except Exception as e:
        print(e)
        print(traceback.print_exc())
        return "Error: " + str(e) + "TRACEBACK: " + traceback.print_exc()

@mcp.tool()
def add_document_to_database(movie_details_information) -> dict:
    """
    Call this tool when the user tells you to add the details of the movie to the database.
    Later call "process_document_for_database" tool. And the argument to the "process_document_for_database" tool is the formatted movie details.
    
    Instructions before you execute this tool:
    0. The user should provide the details on 'User Rating' and 'User Liking (words)' fields. If not then its strictly not allowed to add the details to the database and ask the user to provide the details on 'User Rating' and 'User Liking (words)' fields.
    1. Reformat the 'User Liking (words)' into a full sentence or two that describes the user's emotional response to the movie. Avoid generic or one-word responses. For example, change "Loved it" to "I thoroughly enjoyed the film, especially the emotional storytelling and strong character arcs."
    2. Convert the movie details information to a dictionary.
    3. The the movie details should strictly contain the following keys only.
    4. It is okay to have no fields in the dictionary if the user does not provide any details.
    5. Only after formatting the dictionary pass and call "process_document_for_database" tool.
    
    These are the keys
    ['Movie Name', 'Year', 'Timing(min)', 'Genre', 'Language',
       'Brief Description', 'Cast', 'Director', 'Screenplay/Writer',
       'Production Company', 'Budget in Rupees', 'Revenue in Rupees', 'User Rating', 'User Liking (words)']

    Args:
        movie_details_information (str): Information about the movie provided by the user.
    
    Returns:
        dict: The formatted movie details

        Output Format:
        Below should be the dict movie_details. Maintain the keys in the same order as mentioned in the keys list.
        {
            "ID": "ID", <KEEP IT EMPTY STRING>
            "Movie Name": "Movie Name",
            "Year": "Year",
            "Timing(min)": "Timing(min)",
            "Genre": "Genre",
            "Language": "Language",
            "Brief Description": "Brief Description",
            "Cast": "Cast",
            "Director": "Director",
            "Screenplay/Writer": "Screenplay/Writer",
            "Production Company": "Production Company",
            "Budget in Rupees": "Budget in Rupees",
            "Revenue in Rupees": "Revenue in Rupees",
            "User Liking (words)": "User Liking (words)",
            "User Rating": "User Rating",
            "Embeddings": "Embeddings" <KEEP IT EMPTY STRING>
        }
    """
    try:
        return """
        Instructions before you execute this tool:
        0. The user should provide the details on 'User Rating' and 'User Liking (words)' fields. If not then its strictly not allowed to add the details to the database and ask the user to provide the details on 'User Rating' and 'User Liking (words)' fields.
        1. Reformat the 'User Liking (words)' into a full sentence or two that describes the user's emotional response to the movie. Avoid generic or one-word responses. For example, change "Loved it" to "I thoroughly enjoyed the film, especially the emotional storytelling and strong character arcs."
        2. Convert the movie details information to a dictionary.
        3. The the movie details should strictly contain the following keys only.
        4. It is okay to have no fields in the dictionary if the user does not provide any details.
        5. Only after formatting the dictionary pass and call "process_document_for_database" tool.
        
        These are the keys
        ['Movie Name', 'Year', 'Timing(min)', 'Genre', 'Language',
        'Brief Description', 'Cast', 'Director', 'Screenplay/Writer',
        'Production Company', 'Budget in Rupees', 'Revenue in Rupees', 'User Rating', 'User Liking (words)']
        
        Output Format:
        Below should be the dict movie_details. Maintain the keys in the same order as mentioned in the keys list.
        {
            "ID": "ID", <KEEP IT EMPTY STRING>
            "Movie Name": "Movie Name",
            "Year": "Year",
            "Timing(min)": "Timing(min)",
            "Genre": "Genre",
            "Language": "Language",
            "Brief Description": "Brief Description",
            "Cast": "Cast",
            "Director": "Director",
            "Screenplay/Writer": "Screenplay/Writer",
            "Production Company": "Production Company",
            "Budget in Rupees": "Budget in Rupees",
            "Revenue in Rupees": "Revenue in Rupees",
            "User Liking (words)": "User Liking (words)",
            "User Rating": "User Rating",
            "Embeddings": "Embeddings" <KEEP IT EMPTY STRING>
        }
        """
    except Exception as e:
        print(e)
        print(traceback.print_exc())
        return "Error: " + str(e) + "TRACEBACK: " + traceback.print_exc()


@mcp.tool()
def process_document_for_database(movie_details):
    """
    Call this tool when the user tells you to add the details of the movie to the database.
    Later call "process_document_for_database" tool. And the argument to the "process_document_for_database" tool is the formatted movie details.
    
    Instructions before you execute this tool:
    0. The user should provide the details on 'User Rating' and 'User Liking (words)' fields. If not then its strictly not allowed to add the details to the database and ask the user to provide the details on 'User Rating' and 'User Liking (words)' fields.
    1. Convert the movie details information to a dictionary.
    """
    try:
        print("BEFORE GREYHOUND: ", movie_details)
        if "movie_details" in movie_details.keys():
            if isinstance(movie_details, str):
                movie_details = dict(json.loads(movie_details))["movie_details"]
            else:
                movie_details = dict(movie_details)["movie_details"]

        if isinstance(movie_details, str):
            movie_details = dict(json.loads(movie_details))
        else:
            movie_details = dict(movie_details)

        if "movie_details" in movie_details.keys():
            movie_details = movie_details["movie_details"]
        
        print("AFTER GREYHOUND: ", movie_details)

        gsheet = GoogleSheetUtils(SERVICE_ACCOUNT_FILE_PATH, SPREADSHEET_ID, SHEET_NAME)
        df = gsheet.read_range(range_name = RANGE, as_dataframe = True)
        # Check if dataframe is empty
        if df.empty:
            return "No documents found"
        
        # TODO: NEED TO REMOVE UNNECESSARY FIELDS FROM THE ROW JSON
        movie_details = json.dumps(movie_details)
        embedding = similarity_search_utilities.generate_embedding(movie_details)
        if embedding is not None and len(embedding) > 0:
                embedding_list = embedding.tolist()

        movie_details = dict(json.loads(movie_details))
        movie_details['Embeddings'] = embedding_list
        # UUID
        unique_id = uuid.uuid4()
        movie_details['ID'] = str(unique_id)
        print("AFTER GREYWOLF: ", movie_details)
        
        key_order = [
            "ID", "Movie Name", "Year", "Timing(min)", "Genre", "Language",
            "Brief Description", "Cast", "Director", "Screenplay/Writer",
            "Production Company", "Budget in Rupees", "Revenue in Rupees",
            "User Liking (words)", "User Rating", "Embeddings"
        ]

        # Reorder each dictionary
        ordered_data = {key: movie_details.get(key, None) for key in key_order}

        conversion_map = {
            'ID': str,
            'Year': to_optional_int,
            'Timing(min)': to_optional_float,
            'Budget in Rupees': to_optional_float,
            'Revenue in Rupees': to_optional_float,
            'User Rating': to_optional_float,
        }

        # Apply conversions where needed
        row_data = [
            conversion_map.get(key, str)(value)  # convert using map or fallback to str
            for key, value in ordered_data.items()
        ]

        gsheet.append_row(
            row_data = row_data
        )
        return "Document added to database successfully"
    except Exception as e:
        print(e)
        print(traceback.print_exc())
        return "Error: " + str(e) + "TRACEBACK: " + traceback.print_exc()



if __name__ == "__main__":
    print("Starting MCP server...")
    mcp.run(transport="stdio")

    # # Prevent exit by sleeping indefinitely
    # while True:
    #     time.sleep(60)

# Resources and Prompts are not working in Cursor's Claude
# References
'''
https://github.com/modelcontextprotocol/python-sdk?tab=readme-ov-file
https://smithery.ai/server/@openags/paper-search-mcp
https://docs.astral.sh/uv/getting-started/installation/#shell-autocompletion
https://modelcontextprotocol.io/introduction
https://github.com/modelcontextprotocol/python-sdk
https://github.com/QuantGeekDev/coincap-mcp
'''

'''
uv add -r requirements.txt
uv run --with "mcp[cli]" mcp run /Users/gurudeep/Downloads/My/mcp-example/app/recommendation-system.py

uv run mcp install recommendation-system.py 


'''