# API Services

Services are functions that are called by routes to mutate the database. These are split into files based on which object they interact with in the database, and corresponding to the routes file that typically calls the services. Under the current project structure, routes will handle authentication and request/response validation, but any database mutations will be handled by a corresponding service (under the same file name as the route).
