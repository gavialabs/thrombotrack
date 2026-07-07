# API Routes

Routes defines the endpoints for hitting the REST API. These are split into files based on path which determines the model that the endpoint interacts with. Under the current project structure, routes will handle authentication and request/response validation, but any database mutations will be handled by a corresponding service (under the same file name as the route).