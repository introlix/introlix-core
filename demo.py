import csv
from introlix_api.app.database import feed_data

data = feed_data.find({}, {"_id": 0, "title": 1})  # Exclude _id, include only title

# Specify the CSV file to write to
csv_file = 'feed_data_titles.csv'

# Write data to a CSV file
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    
    # Write header (just the title field)
    writer.writerow(["title"])
    
    # Write each document's title to the CSV
    for document in data:
        writer.writerow([document.get("title")])

print(f"Title data successfully saved to {csv_file}")