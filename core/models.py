from django.db import models


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class BaseHistory(models.Model):
    """
    Base class for all other history views.
    """

    # You'll need to either set these attributes.
    states_choices = None

    # Model fields
    reason = models.CharField(max_length=250, blank=True, null=True)
    date = models.DateTimeField(auto_now_add=True)
    state = models.CharField(max_length=30)

    class Meta:
        abstract = True
        verbose_name = "History"
        verbose_name_plural = "Histories"

    def __str__(self):
        return "{}".format(self.state)

    def get_state_display(self):
        """
        :return: the value associated with the state, or `None`.
        """
        assert (
            self.states_choices is not None
        ), "'{}' should either include a `states_choices` attribute, ".format(
            self.__class__.__name__
        )
        return dict(self.states_choices).get(self.state)
