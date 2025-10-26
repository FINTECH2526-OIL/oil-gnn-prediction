# resource "google_vertex_ai_endpoint" "my_model_endpoint" {
#     name = "my_model_endpoint"
#   project = "your-gcp-project-id"
#   location = "your-gcp-region"
#   display_name = "my-model-endpoint"
#   description = "Endpoint for my custom model"
# }

# resource "google_vertex_ai_model" "my_custom_model" {
#   project = "your-gcp-project-id"
#   location = "your-gcp-region"
#   display_name = "my-custom-model"
#   description = "A custom model for inference"
#   artifact_uri = "gs://your-model-bucket/your-model-path/" # Path to your model artifact
#   container_spec {
#     image_uri = "gcr.io/cloud-aiplatform/prediction/tf2-cpu.2-8:latest" # Or your custom container image
#     command = ["python", "main.py"] # Optional: entry point command
#     args = ["--model_dir=/model"] # Optional: arguments for the entry point
#   }
# }

# resource "google_vertex_ai_model_deployment" "my_model_deployment" {
#   project = "your-gcp-project-id"
#   location = "your-gcp-region"
#   endpoint = google_vertex_ai_endpoint.my_model_endpoint.id
#   model = google_vertex_ai_model.my_custom_model.id
#   deployed_model_id = "my-deployed-model-id" # Unique ID for the deployed model

#   dedicated_resources {
#     machine_spec {
#       machine_type = "n1-standard-4"
#     }
#     min_replica_count = 1
#     max_replica_count = 1
#   }
#   traffic_split = {
#     "0" = 100 # 100% traffic to this deployed model
#   }
# }