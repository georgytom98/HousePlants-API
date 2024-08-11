# Houseplants-api

1. Token Authenticate user to start using the plant API:
    - Go to: user > POST:/api/user/create endpoint
    - Try it out > Enter your info > Execute
    - After creating user, go to: user > POST:/api/user/token
    - Try it out > Enter user credentials > Execute
    - From the response body, copy your token
    - Next, select the 'Authorize' button at the top right of the API page
    - Scroll down to 'tokenAuth(apiKey)'
    - Type 'Token' followed by the copied token id,
        e.g., "Token ae23fd3f3saf..."
        and click Authorize to authorize the user
        
2. Workflow of using Plants API:
    - Go to POST:/api/plant/plants/ to create your plant
    - View all your plants at GET:/api/plant/plants or see one of
    your specific plants by id at GET:/api/plant/plants/{id}
    - Update, delete, or create individual Tags and Care Tips for
    your plant at the respective endpoints
    - If you are uploading images along with your plant details,
    then change the form type to 'multipart/form-data' at the
    respective endpoint
    - Additionally, you can add images to your plant
    at POST:/api/plant/plants/{id}/upload-image/ endpoint
    - Explore various endpoints and features!
    - HousePlants API Schema can be downloaded by clicking on
    /api/schema/ at the top left corner

Thank you for visiting Georgy's Houseplant API!
