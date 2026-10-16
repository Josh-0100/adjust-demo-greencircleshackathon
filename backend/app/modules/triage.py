from app.modules.base import CivicModule, Classification, category_match


class Triage(CivicModule):
    id = "triage"
    name = "Council Enquiry Triage"
    description = "Suggest a category, department and priority for a staff review."
    icon = "GitBranch"
    input_hint = "Describe the issue, location context and any immediate risk."
    example_prompt = "There is a pothole on the road outside my home and cyclists could be injured."
    capabilities = ["Category suggestions", "Department routing", "Priority suggestions", "Potential duplicate detection", "Staff review"]
    workflow_steps = ["Classify issue", "Suggest a department", "Check potential duplicates", "Route to human review"]
    resource_modules = ["triage", "service-navigator"]

    def classify(self, message):
        return category_match(message, [
            (["pothole", "road", "pavement", "street", "cycle"], Classification("Roads and public space", "Highways Review", "Route a public-space report", True)),
            (["bin", "waste", "rubbish", "recycling", "collection"], Classification("Waste and recycling", "Neighbourhood Services", "Route a waste enquiry")),
            (["housing", "home", "damp", "mould", "cold", "rent"], Classification("Housing and wellbeing", "Housing Support", "Route a housing enquiry", True)),
        ], Classification("General enquiry", "Resident Services", "Route an enquiry"))

