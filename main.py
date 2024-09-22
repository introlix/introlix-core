import subprocess

def run_app():
    command = ["scrapy", "crawl", "generic"]
    working_directory = "src/introlix_api/app/introlix_spider"

    result = subprocess.run(command, cwd=working_directory, capture_output=True, text=True)

    print("Output:", result.stdout)
    print("Error:", result.stderr)

if __name__ == "__main__":
    # running the spider
    run_app()