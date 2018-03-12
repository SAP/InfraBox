from pyinfraboxutils.ibrestplus import api

project = api.namespace('api/v1/projects/',
                        description='Project related operations')

settings = api.namespace('api/v1/settings/',
                         description='Settings')

user = api.namespace('api/v1/user/',
                     description='User')

account = api.namespace('api/v1/account/',
                        description='Account')

github = api.namespace('api/v1/github/',
                       description='GitHub')

github_auth = api.namespace('github/',
                            description='GitHub Auth')
