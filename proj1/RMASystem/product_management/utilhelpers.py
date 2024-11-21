from model_utils import Choices



# move some predefined settings to here
PRIORITY_LEVEL_CHOICES = Choices(
    ('normal', 'Normal'),
    ('hot', 'Hot'),
    ('zfa', 'ZFA')
)

STATUS_CHOICES = Choices(
    ('new', 'New'),
    ('in_progress', 'In Progress'),
    ('completed', 'Completed'),
    ('archived', 'Archived')
)