import requests

def fetch_hashnode_posts(page=1, per_page = 10, tag = ''):
    all_posts = []
    has_next_page = True
    end_cursor = None
    posts_per_page = per_page  # Number of posts per page

    # Calculate the number of posts to skip based on the requested page
    skip_count = (page - 1) * posts_per_page

    while has_next_page:
        # Construct the GraphQL query with the specified number of posts per page
        query = {
            "query": f"""
            query Publication {{
                publication(host: "blog.developerdao.com") {{
                    title
                    posts(first: {posts_per_page}, after: {f'"{end_cursor}"' if end_cursor else 'null'}) {{
                        edges {{
                            node {{
                                title
                                brief
                                url
                                publishedAt
                                tags {{
                                    id
                                    name
                                }}
                                coverImage {{
                                    url
                                }}
                            }}
                        }}
                        pageInfo {{
                            endCursor
                            hasNextPage
                        }}
                    }}
                }}
            }}"""
        }

        # Make the POST request to the Hashnode GraphQL endpoint
        response = requests.post("https://gql.hashnode.com/", json=query)

        # Check for request success
        if response.status_code == 200:
            data = response.json()
            posts = data['data']['publication']['posts']['edges']

            # Append fetched posts to the all_posts list
            all_posts.extend([edge['node'] for edge in posts])

            # Update pagination info
            page_info = data['data']['publication']['posts']['pageInfo']
            end_cursor = page_info['endCursor']
            has_next_page = page_info['hasNextPage']

            # Stop if we've fetched enough posts
            if len(all_posts) >= skip_count + posts_per_page:
                break
        else:
            print(f"Error: {response.status_code} - {response.text}")
            break

    # Return only the posts for the requested page
    if tag == 'bitcoin' or tag == 'web3':
        return all_posts[skip_count:skip_count + posts_per_page]