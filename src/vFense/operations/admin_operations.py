#!/usr/bin/env python

from vFense import logging
from time import time
from vFense.operations._db_model import (
    AdminOperationKey
)
from vFense.operations._constants import vFenseObjects, OperationErrors
from vFense.core._db_constants import DbTime

from vFense.operations._db_admin import (
    fetch_admin_operation, insert_admin_operation,
    update_admin_operation
)

from vFense.errorz.status_codes import (
    DbCodes
)

class AdminOperationManager(object):
    """This is what creates operations for an agent or multiple agents.

    """
    def __init__(self, username, view_name):
        """
        Args:
            username (str): the name of the user who created the operation.
            view_name (str): the name of the view this user is part of.

        Basic Usage:
            >>> from vFense.operations.admin_operations import AdminOperation
            >>> username = 'global_admin'
            >>> view_name = 'global'
            >>> oper = AdminOperation(username, view_name)
        """
        self.username = username
        self.view_name = view_name
        self.now = time()
        self.db_time = DbTime.time_now()
        self.INIT_COUNT = 0


    def create(self, action, performed_on):
        """Create the operation and return the operation_id.
        Args:
            action (str): The action that was performed.
                (create view, create user, remove user, etc..).
            performed_on (str): The entity this action was performed on.
                (tag, agent, user, view, group)

        Basic Usage:
            >>> from vFense.operations.admin_operations import AdminOperation
            >>> username = 'global_admin'
            >>> view_name = 'global'
            >>> oper = AdminOperation(username, view_name)
            >>> action = 'create user'
            >>> performed_on = 'user'
            >>> oper.create(action, performed_on)

        Returns:
            String The 36 character UUID of the operation that was created.
            6c0209d5-b350-48b7-808a-158ddacb6940
        """

        data = (
            {
                AdminOperationKey.Action: action,
                AdminOperationKey.PerformedOn: performed_on,
                AdminOperationKey.CurrentView: self.view_name,
                AdminOperationKey.CreatedBy: self.username,
                AdminOperationKey.CreatedTime: self.db_time,
                AdminOperationKey.CompletedTime: DbTime.begining_of_time(),
            }
        )
        status_code, _, _, generated_ids = (
            insert_admin_operation(data)
        )
        if status_code == DbCodes.Inserted:
            operation_id = generated_ids[0]

        else:
            operation_id = None

        return operation_id


    def update(self, operation_id, **kwargs):
        """Update the operation with the results.
        Args:
            operation_id (str): The UUID of the operation.

        Kwargs:
            status_message (str): The status message.
            generic_status_code (int): The generic status code.
            vfense_status_code (int): The vfense status code.
            errors (list): List of dictionaires with errors.
            completed_time (int): The time this operation was created.
            object_data (dict): Dictionary of data related to the object.
                example: {'name': 'Global Group', 'id': ''}
            ids_created (list): List of the ids that were generated.
            ids_updated (list): List of ids that were updated.
            ids_removed (list): List of ids that were removed.

        Basic Usage:
            >>> from vFense.operations.admin_operations import AdminOperation
            >>> username = 'global_admin'
            >>> view_name = 'global'
            >>> oper = AdminOperation(username, view_name)
            >>> action = 'create user'
            >>> performed_on = 'user'
            >>> oper.create(action, performed_on)

        Returns:
            String The 36 character UUID of the operation that was created.
            6c0209d5-b350-48b7-808a-158ddacb6940
        """

        data = (
            {
                AdminOperationKey.ObjectData: (
                    kwargs.get(AdminOperationKey.ObjectData, {})
                ),
                AdminOperationKey.CompletedTime: DbTime.begining_of_time(),
                AdminOperationKey.StatusMessage: (
                    kwargs.get(AdminOperationKey.StatusMessage)
                ),
                AdminOperationKey.GenericStatusCode: (
                    kwargs.get(AdminOperationKey.GenericStatusCode)
                ),
                AdminOperationKey.VfenseStatusCode: (
                    kwargs.get(AdminOperationKey.VfenseStatusCode)
                ),
                AdminOperationKey.Errors: (
                    kwargs.get(AdminOperationKey.Errors, {})
                ),
                AdminOperationKey.IdsCreated: (
                    kwargs.get(AdminOperationKey.IdsCreated, [])
                ),
                AdminOperationKey.IdsUpdated: (
                    kwargs.get(AdminOperationKey.IdsUpdated, [])
                ),
                AdminOperationKey.IdsRemoved: (
                    kwargs.get(AdminOperationKey.IdsRemoved, [])
                ),
            }
        )
        status_code, _, _, generated_ids = (
            update_admin_operation(data)
        )
        if status_code == DbCodes.Inserted:
            operation_id = generated_ids[0]

        else:
            operation_id = None

        return operation_id

