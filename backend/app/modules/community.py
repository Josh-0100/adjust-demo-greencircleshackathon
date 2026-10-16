from app.modules.base import CivicModule, Classification, category_match, extract_skills
from app.schemas.api import Recommendation


class Community(CivicModule):
    id = "community"
    name = "Community Resource Discovery"
    description = "Find fictional local support and volunteer activities by borough."
    icon = "Users"
    input_hint = "Tell us the support or activity you are looking for and your interests."
    example_prompt = "I would like to volunteer in a community garden and meet people near me."
    capabilities = ["Borough filtering", "Community support discovery", "Volunteer matching"]
    workflow_steps = ["Identify interests", "Filter local resources", "Explain matches", "Confirm availability with a human"]
    resource_modules = ["community"]

    def classify(self, message):
        return category_match(message, [
            (["volunteer", "garden", "help out"], Classification("Volunteering", "Community Partnerships", "Find a volunteer activity")),
            (["food", "pantry", "support", "lonely", "meet people"], Classification("Community support", "Community Partnerships", "Find local support", True)),
        ], Classification("Community activity", "Community Partnerships", "Discover a local resource"))

    def recommend(self, message, resources):
        existing = set(extract_skills(message))
        return [Recommendation(title=r.title, description=r.description, next_steps=r.next_steps,
                               match_score=round(100 * len(set(r.skills) & existing) / len(r.skills)) if r.skills else None,
                               skills_gap=[]) for r, _ in resources[:3]]

