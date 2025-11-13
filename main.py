import http.client
import json

conn = http.client.HTTPSConnection("fresh-linkedin-profile-data.p.rapidapi.com")

headers = {
    'x-rapidapi-key': "977b42cd32msh8cac1685e50cac9p14f609jsn7804286dd934",
    'x-rapidapi-host': "fresh-linkedin-profile-data.p.rapidapi.com"
}

# Assuming the endpoint for profile comments is /get-profile-comments
# With parameter url for the profile
conn.request("GET", "/get-profile-comments?url=https://www.linkedin.com/in/noureddinemr1/", headers=headers)

res = conn.getresponse()
data = res.read()

response = json.loads(data.decode("utf-8"))

# Assuming the response has a 'comments' list
if 'comments' in response:
    comments = response['comments'][:10]  # Get first 10 comments
    for i, comment in enumerate(comments, 1):
        print(f"{i}. {comment}")
else:
    print("No comments found or different response structure.")
    print(data.decode("utf-8"))
