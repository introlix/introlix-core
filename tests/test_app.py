from introlix_api.app.appwrite import get_interests


def test_get_interests():
    response = get_interests()
    for interest in response:
        print(interest['interest'])
        print(interest['keywords'])

test_get_interests()