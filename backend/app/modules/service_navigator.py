from app.modules.base import CivicModule, Classification, category_match


class ServiceNavigator(CivicModule):
    id = "service-navigator"
    name = "Council Service Navigator"
    description = "Find relevant support, inspect sources and prepare safe next steps."
    icon = "Compass"
    input_hint = "Describe what you need help with, including your borough."
    example_prompt = "My home is cold and I am struggling with energy bills. Where can I find support?"
    capabilities = ["Source-backed service discovery", "Next-step guidance", "Human eligibility review"]
    workflow_steps = ["Understand need", "Retrieve approved sources", "Recommend next steps", "Flag human review"]
    resource_modules = ["service-navigator"]

    def classify(self, message):
        return category_match(message, [
            (["home", "housing", "rent", "cold", "damp", "mould", "homeless"], Classification("Housing and wellbeing", "Housing Support", "Find housing support", True)),
            (["benefit", "money", "bill", "debt", "income", "payment"], Classification("Money and bills", "Resident Support", "Find money guidance", True)),
            (["bin", "waste", "recycling", "collection"], Classification("Waste and recycling", "Neighbourhood Services", "Find waste guidance")),
        ], Classification("General support", "Resident Services", "Find a relevant service"))

