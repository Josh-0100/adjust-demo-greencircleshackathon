from .models import Analysis, Recommendation
from .knowledge import KnowledgeLibrary

# Authored discussion options. Providers cannot write or override these templates.
# The steps are applications of the cited guidance, not individual professional instructions.
TEMPLATES = [
    dict(id="handling-review", topics=["manual"], title="Review the lifting task together", barrier="Reported difficulty with manual handling", sources=["H01", "H04", "H05"],
         steps=["Walk through the difficult handling tasks with the employee and a competent risk assessor.", "Identify handling that can be avoided and assess remaining risks before agreeing changes."],
         question="Which lifts or movements are hardest, and when?", effort="Review the task",
         limitation="This is not a lifting assessment or a statement that any load is safe.", referral="Use a competent manual handling assessor; seek occupational health advice for individual work limitations."),
    dict(id="lifting-aids", topics=["manual"], title="Explore suitable handling equipment", barrier="Repeated lifting or moving loads", sources=["H02", "H03"],
         steps=["Ask a competent assessor whether the handling can be removed or assisted mechanically.", "Check equipment suitability, space, training and maintenance before any trial."],
         question="Could a change in the way stock moves reduce difficult lifts?", effort="Explore equipment",
         limitation="Do not choose equipment from this suggestion alone. Suitability and safe use need assessment.", referral="A competent equipment or handling adviser can assess a suitable solution."),
    dict(id="loads-layout", topics=["manual"], title="Revisit loads, layout and work pace", barrier="Awkward or repetitive handling demands", sources=["H06", "H07"],
         steps=["Explore smaller loads, shorter routes or a layout that reduces awkward movements.", "Discuss a realistic handling pace and assess the changes before use."],
         question="Which change to the load, route or pace might make the biggest difference?", effort="Review the task",
         limitation="A lighter load is not automatically safe. Assess the whole task and individual circumstances.", referral="Refer unresolved handling risks to a competent health and safety adviser."),
    dict(id="workload", topics=["stress", "concentration"], title="Make priorities and deadlines clearer", barrier="Workload, pressure or difficulty concentrating", sources=["A10", "H10"],
         steps=["Discuss which demands are difficult and agree a short list of priorities.", "Explore smaller task steps and realistic deadlines, then review together."],
         question="Which demands feel hardest, and what would make priorities clearer?", effort="Start with a conversation",
         limitation="An individual conversation does not replace assessment of wider work-related stress risks.", referral="Consider occupational health input if suitable changes remain unclear."),
    dict(id="quiet-workspace", topics=["sensory", "stress"], title="Explore a quieter place to work", barrier="Noise, distraction or environmental demands", sources=["A11", "A01"],
         steps=["Ask whether a quieter location or rest area would help.", "Check task needs and practical space before agreeing a trial."],
         question="Would a different work area help, and what would you want it to be like?", effort="Start with a conversation",
         limitation="A quieter area may not suit every role or person. Discuss rather than assume.", referral="Seek specialist workplace advice if environmental barriers cannot be resolved."),
    dict(id="check-ins", topics=["stress", "communication"], title="Agree how to communicate and check in", barrier="Difficult communication or unpredictable demands", sources=["A12", "A03"],
         steps=["Ask about useful communication methods and a manageable check-in pattern.", "Agree how priorities and changes will be shared."],
         question="How would you prefer us to share instructions and check in?", effort="Start with a conversation",
         limitation="Agree what may be shared with others and respect the employee's privacy.", referral="For hearing or other specialist communication needs, discuss occupational health or Access to Work advice."),
    dict(id="workstation", topics=["desk"], title="Review the workstation and work routine", barrier="Difficulty or discomfort during computer or seated work", sources=["H08", "H09"],
         steps=["Arrange an appropriate workstation assessment covering equipment, furniture and work conditions.", "Have a trained assessor review findings and agree practical changes."],
         question="Which parts of the workstation or routine make tasks difficult?", effort="Review the task",
         limitation="This tool cannot prescribe a chair, posture or medical treatment.", referral="Use a trained DSE assessor; discuss occupational health advice for individual needs."),
    dict(id="working-patterns", topics=["fatigue", "stress"], title="Discuss breaks and working patterns", barrier="Difficulty sustaining the current work pattern", sources=["A02", "A01"],
         steps=["Ask which times or routines create barriers.", "Explore a suitable pattern of work or breaks and agree how to review it."],
         question="Would a change to breaks or working times help you do your work?", effort="Start with a conversation",
         limitation="Do not set medical limits or promise a particular arrangement; assess practical needs together.", referral="Seek occupational health advice where work limitations need specialist assessment."),
    dict(id="access-layout", topics=["mobility"], title="Explore access and task arrangements", barrier="Difficulty moving around or using the work area", sources=["A02", "G01"],
         steps=["Discuss the parts of the workplace or task that are difficult to access.", "Explore a suitable layout, location or distribution of tasks and obtain specialist advice where needed."],
         question="Which places or tasks are difficult to access, and what has helped before?", effort="Review the task",
         limitation="Building, evacuation and equipment changes need appropriate assessment.", referral="Consider an access specialist or occupational health adviser for unresolved barriers."),
]


def recommend(analysis: Analysis, library: KnowledgeLibrary, today):
    index = {entry.id: entry for entry in library.retrieve(analysis.scenarios, today)}
    candidates = []
    for item in TEMPLATES:
        if not set(item["topics"]).intersection(analysis.scenarios):
            continue
        if not all(source in index for source in item["sources"]):
            continue
        candidates.append(Recommendation(id=item["id"], title=item["title"], barrier_addressed=item["barrier"],
                                         steps=item["steps"], employee_questions=[item["question"]], source_ids=item["sources"],
                                         limitations=item["limitation"], referral_guidance=item["referral"], effort=item["effort"]))
    # Cover different barriers before offering more options for the same task.
    candidates.sort(key=lambda rec: sum(len(set(item["topics"]).intersection(analysis.scenarios))
                                       for item in TEMPLATES if item["id"] == rec.id), reverse=True)
    return candidates[:6]
