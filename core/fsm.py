import logging

logger = logging.getLogger(__name__)


class WrongState(Exception):
    pass


class FiniteStateMachine:
    """
    Mixins which adds the behavior of a state_machine.

    Represents the state machine for the object
    The states and transitions should be specified.
    {
       'pending': next_states_tuples or '__all__'
    }
    """

    state_machine = None
    class_history = None

    def get_state(self):
        return self.state

    def can_change(self, next_state):
        """
        Validates if the next_state can be executed or not.

        It uses the state_machine attribute in the class.
        """
        valid_transitions = self.get_valid_transitions()

        if not valid_transitions:
            return False

        return next_state in valid_transitions

    def get_valid_transitions(self):
        """
        Return possible states to whom a product can transition.

        @return {tuple/list}
        """
        current = self.get_state()

        valid_transitions = self.state_machine.get(current)

        if valid_transitions == "__all__":
            return self.state_machine.keys()

        return self.state_machine.get(current, ())

    def on_change_state(self, previous_state, next_state, **kwargs):
        """
        Called everytime an state changes.

        @param {str/int} previous_state
        @param {str/int} next_state
        Useful for catch events related with emails and others things.
        """
        pass

    def change_state(self, next_state, auto_save: bool = True, **kwargs) -> None:
        """
        Performs a transition from current state to next state if possible.

        @param {str/int} next_state
        """

        current_state = self.get_state()

        if self.can_change(next_state):
            name = "on_before_{0}_callback".format(next_state)
            callback = getattr(self, name, None)
            # record this change in historic
            if callback:
                callback(**kwargs)

            self.state = next_state
            self.on_change_state(current_state, next_state, **kwargs)
            if self.class_history:
                self.create_history(**kwargs)
            if auto_save:
                self.save()
                # This was added because in some cases, a Model is instanciated
                # but not saved, and there are some operations that require
                # the existance of the instance.

            name = "on_{0}_callback".format(next_state)
            callback = getattr(self, name, None)
            if callback:
                callback(**kwargs)
        else:
            msg = "The transition from {0} to {1} is not valid".format(
                current_state, next_state
            )
            raise WrongState(msg)

    def create_history(self, **kwargs) -> None:
        # TODO create history for state
        pass
        # self.class_history.create(self, **kwargs)
