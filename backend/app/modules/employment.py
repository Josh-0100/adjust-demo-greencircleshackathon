from app.modules.base import CivicModule, Classification, extract_skills
from app.schemas.api import Recommendation


class Employment(CivicModule):
    id = "employment"
    name = "Employment and Skills Matching"
    description = "Explain opportunity matches and identify skills to develop."
    icon = "BriefcaseBusiness"
    input_hint = "Share experience, existing skills and the kind of work you would like."
    example_prompt = "I have retail and customer service experience. I want office work but need to learn spreadsheets."
    capabilities = ["Skills extraction", "Explainable match scores", "Skills gaps", "Training pathways"]
    workflow_steps = ["Extract stated skills", "Match catalogued opportunities", "Identify skill gaps", "Prepare a reviewed pathway"]
    resource_modules = ["employment", "learning"]

    def classify(self, message):
        return Classification("Employment and skills", "Employment Support", "Match skills to opportunities", True)

    def recommend(self, message, resources):
        existing = set(extract_skills(message))
        recommendations = []
        for resource, _ in resources:
            if resource.module_id != "employment":
                continue
            needed = set(resource.skills)
            gap = sorted(needed - existing)
            match = round(100 * len(needed & existing) / len(needed)) if needed else None
            steps = resource.next_steps + ([f"Discuss a training plan for: {', '.join(gap)}."] if gap else [])
            recommendations.append(Recommendation(title=resource.title, description=resource.description,
                                                  next_steps=steps, match_score=match, skills_gap=gap))
        return sorted(recommendations, key=lambda item: item.match_score or 0, reverse=True)[:3]

    def explain(self, message):
        skills = extract_skills(message)
        return f"Stated skills: {', '.join(skills) if skills else 'none verified from this message'}. Match scores equal the share of catalogue skills explicitly mentioned; they are not hiring or eligibility scores."

