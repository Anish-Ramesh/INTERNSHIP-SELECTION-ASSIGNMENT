import pandas as pd
import os

def clear_directory(folder_path):
    if os.path.exists(folder_path):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                pass
    else:
        os.makedirs(folder_path, exist_ok=True)

def main():
    print("=== Dataset Preprocessor ===")
    print("Please select an option:")
    print("1. Use existing datasets (top1000movies.csv and rotten_tomatoes_movies.csv)")
    print("2. Upload separate primary and secondary custom datasets")
    print("3. Upload a single preprocessed custom dataset containing all columns")
    
    choice = input("\nEnter your choice (1/2/3) [1]: ").strip()
    if choice == '' or choice == '1':
        print("\n--- Using Existing Datasets ---")
        primary_path = 'dataset/top1000movies.csv'
        secondary_path = 'dataset/rotten_tomatoes_movies.csv'
        
        primary_col_title = 'Title'
        primary_col_gross = 'Gross'
        primary_col_rating = 'rottenRating'
        
        secondary_col_title = 'movie_title'
        secondary_col_review = 'critics_consensus'
        
        try:
            primary_df = pd.read_csv(primary_path)
            secondary_df = pd.read_csv(secondary_path)
        except FileNotFoundError as e:
            print(f"Error: Could not find required existing dataset: {e}")
            return
            
        secondary_df = secondary_df.dropna(subset=[secondary_col_review, secondary_col_title])
        merged = pd.merge(primary_df, secondary_df, left_on=primary_col_title, right_on=secondary_col_title, how='inner')
        
        if merged[primary_col_gross].dtype == object:
            merged['Gross_clean'] = merged[primary_col_gross].replace('[\$,]', '', regex=True)
        else:
            merged['Gross_clean'] = merged[primary_col_gross]
            
        merged = merged.dropna(subset=['Gross_clean', primary_col_rating])
        merged['Gross_clean'] = merged['Gross_clean'].astype(float)
        
        merged['computed_budget'] = ''
        merged['computed_week_open'] = merged['Gross_clean'] / 60
        merged['computed_gross'] = merged['Gross_clean']
        merged['computed_rating'] = merged[primary_col_rating]
        merged['computed_review'] = merged[secondary_col_review]
        merged['computed_title'] = merged[primary_col_title]

    elif choice == '2':
        print("\n--- Custom Separate Datasets ---")
        print("Note: The PRIMARY dataset MUST contain these columns: 'movie title', 'gross', 'week open', 'budget', 'rotten_rating'")
        primary_path = input("Enter path to PRIMARY dataset CSV: ").strip()
        print("\nNote: The SECONDARY dataset MUST contain these columns: 'movie title', 'movie_review'")
        secondary_path = input("Enter path to SECONDARY dataset CSV: ").strip()
        
        try:
            primary_df = pd.read_csv(primary_path)
            secondary_df = pd.read_csv(secondary_path)
        except FileNotFoundError as e:
            print(f"Error: Could not find dataset: {e}")
            return
            
        req_prim = ['movie title', 'gross', 'week open', 'budget', 'rotten_rating']
        missing_prim = [col for col in req_prim if col not in primary_df.columns]
        if missing_prim:
            print(f"Error: Primary dataset is missing mandatory columns: {missing_prim}")
            return
            
        req_sec = ['movie title', 'movie_review']
        missing_sec = [col for col in req_sec if col not in secondary_df.columns]
        if missing_sec:
            print(f"Error: Secondary dataset is missing mandatory columns: {missing_sec}")
            return
            
        secondary_df = secondary_df.dropna(subset=['movie_review', 'movie title'])
        merged = pd.merge(primary_df, secondary_df, on='movie title', how='inner')
        merged = merged.dropna(subset=['gross', 'rotten_rating'])
        
        merged['computed_budget'] = merged['budget']
        merged['computed_week_open'] = merged['week open']
        merged['computed_gross'] = merged['gross']
        merged['computed_rating'] = merged['rotten_rating']
        merged['computed_review'] = merged['movie_review']
        merged['computed_title'] = merged['movie title']

    elif choice == '3':
        print("\n--- Single Preprocessed Dataset ---")
        print("Note: The SINGLE dataset MUST contain all these mandatory columns:")
        print("'movie title', 'gross', 'week open', 'budget', 'rotten_rating', 'movie_review'")
        single_path = input("Enter path to the single dataset CSV: ").strip()
        
        try:
            merged = pd.read_csv(single_path)
        except FileNotFoundError as e:
            print(f"Error: Could not find dataset: {e}")
            return
            
        req_all = ['movie title', 'gross', 'week open', 'budget', 'rotten_rating', 'movie_review']
        missing_all = [col for col in req_all if col not in merged.columns]
        if missing_all:
            print(f"Error: Single dataset is missing mandatory columns: {missing_all}")
            return
            
        merged = merged.dropna(subset=['movie_review', 'movie title', 'gross', 'rotten_rating'])
        
        merged['computed_budget'] = merged['budget']
        merged['computed_week_open'] = merged['week open']
        merged['computed_gross'] = merged['gross']
        merged['computed_rating'] = merged['rotten_rating']
        merged['computed_review'] = merged['movie_review']
        merged['computed_title'] = merged['movie title']
        
    else:
        print("Invalid choice. Exiting.")
        return

    print("\n------------------------------")
    num_files_str = input("How many text files should be generated for the unstructured data? [15]: ").strip()
    num_files_to_generate = 15 if not num_files_str else int(num_files_str)

    print("\nProcessing...")
    
    # Write structured CSV
    structured_df = pd.DataFrame()
    structured_df['Title'] = merged['computed_title']
    structured_df['budget'] = merged['computed_budget']
    structured_df['opening weekend'] = merged['computed_week_open']
    structured_df['worldwide gross'] = merged['computed_gross']
    structured_df['Rotten Tomatoes score'] = merged['computed_rating']
    
    structured_path = 'dataset/movies_structured.csv'
    try:
        structured_df.to_csv(structured_path, index=False)
        print(f"Saved {len(structured_df)} matched rows into {structured_path}")
    except PermissionError:
        print(f"Skipped saving {structured_path} as it is open or permission is denied (left as is).")

    # Generate Unstructured Reviews
    unstructured_dir = 'dataset/unstructured_reviews'
    clear_directory(unstructured_dir)
    os.makedirs(unstructured_dir, exist_ok=True)
    
    files_created = 0
    for index, row in merged.iterrows():
        if files_created >= num_files_to_generate:
            break
            
        title = row['computed_title']
        cc = row['computed_review']
        txt_content = f"movie: {title}\nreview: {cc}\n"
        
        safe_title = str(title).replace(':', '').replace('/', '_').replace('?', '').replace('*', '').replace('"', '').replace('<', '').replace('>', '').replace('|', '')
        file_path = os.path.join(unstructured_dir, f"{safe_title}.txt")
        
        file_existed = os.path.exists(file_path)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(txt_content)
            
        if not file_existed:
            files_created += 1

    print(f"Created {files_created} text files in {unstructured_dir} directory.")
    print("Done!")

if __name__ == "__main__":
    main()
