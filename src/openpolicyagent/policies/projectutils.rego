package infrabox

import data.infrabox.collaborators.collaborators
import data.infrabox.projects.projects

project_owner([user, project]){
    collaborators[i].project_id = project
    collaborators[i].user_id = user
    collaborators[i].role = "Owner"
}

project_collaborator([user, project]){
    collaborators[i].project_id = project
    collaborators[i].user_id = user
}

project_public(project){
    projects[i].id = project
    projects[i].public = true
}

