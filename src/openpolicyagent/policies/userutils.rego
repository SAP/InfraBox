package infrabox

# HTTP API request
import input as api

user_valid(token){
    token.type = "user"
    token.user_id != ""
}

user_id[token]{
    token.user_id
}