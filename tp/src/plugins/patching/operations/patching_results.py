#!/usr/bin/env python
import logging
import logging.config

from vFense.core._constants import CommonKeys
from vFense.core.decorators import results_message
from vFense.core.agent import AgentKey
from vFense.errorz._constants import ApiResultKeys
from vFense.operations._constants import AgentOperations
from vFense.operations.results import OperationResults

from vFense.errorz.status_codes import AgentOperationCodes, GenericCodes, \
    GenericFailureCodes, AgentFailureResultCodes, AgentResultCodes

from vFense.plugins.patching._constants import SharedAppKeys, CommonAppKeys
from vFense.plugins.patching.rv_db_calls import *

from vFense.plugins.patching.os_apps.incoming_updates import \
    incoming_packages_from_agent

logging.config.fileConfig('/opt/TopPatch/conf/logging.config')
logger = logging.getLogger('rvapi')

class PatchingOperationResults(OperationResults):
    """This will update the results of an install, uninstall,
        and refresh_apps, as well as update the operation itself.
    """

    def apps_refresh(self):
        oper_type = AgentOperations.REFRESH_APPS
        results = self.update_operation(oper_type)
        return(results)

    def install_os_apps(
        self, app_id, reboot_required,
        apps_to_delete, apps_to_add
        ):
        self._set_global_properties(
            app_id, reboot_required,
            apps_to_delete, apps_to_add
        )
        self.CurrentAppsCollection = AppCollections.UniqueApplications
        results = self._update_app_status()
        return(results)

    def install_custom_apps(
        self, app_id, reboot_required,
        apps_to_delete, apps_to_add
        ):
        self._set_global_properties(
            app_id, reboot_required,
            apps_to_delete, apps_to_add
        )
        self.CurrentAppsCollection = AppCollections.CustomApps
        results = self._update_app_status()
        return(results)

    def install_supported_apps(
        self, app_id, reboot_required,
        apps_to_delete, apps_to_add
        ):
        self._set_global_properties(
            app_id, reboot_required,
            apps_to_delete, apps_to_add
        )
        self.CurrentAppsCollection = AppCollections.SupportedApps
        results = self._update_app_status()
        return(results)

    def install_agent_apps(
        self, app_id, reboot_required,
        apps_to_delete, apps_to_add
        ):
        self._set_global_properties(
            app_id, reboot_required,
            apps_to_delete, apps_to_add
        )
        self.CurrentAppsCollection = AppCollections.AgentApps
        results = self._update_app_status()
        return(results)

    def _set_global_properties(
        self, app_id, reboot_required,
        apps_to_delete, apps_to_add
        ):
        """Set global properties
        Args:
            app_id (str): The application id.
            reboot_required (str):  true or false
            apps_to_delete (list): list of dictionaires,
                [{"app_name": "foo", "app_version": "1.2.3"}]
            apps_to_add (list): list of dictionaires,

        Attributes:
            self.app_id
            self.reboot_required
            self.apps_to_delete
            self.apps_to_add
            self.oper_type
        """

        self.apps_to_add = apps_to_add
        self.apps_to_delete = apps_to_delete
        self.app_id = app_id
        self.reboot_required = reboot_required
        self.oper_type = self.operation_data[OperationKey.Operation]

    def _apps_to_add(self):
        """Add apps to agent
        """
        try:
            self.apps_to_add = [loads(x) for x in self.apps_to_add]
        except Exception as e:
            pass

        incoming_packages_from_agent(
            self.username, self.agent_id,
            self.customer_name,
            self.agent_data[AgentKey.OsCode],
            self.agent_data[AgentKey.OsString],
            self.apps_to_add, delete_afterwards=False
        )

    def _apps_to_delete(self):
        """Delete apps from agent
        """
        try:
            self.apps_to_delete = [loads(x) for x in self.apps_to_delete]
        except Exception as e:
            pass

        for apps in apps_to_delete:
            delete_app_from_agent(
                apps[NAME],
                apps[VERSION],
                self.agent_id
            )

    @results_message
    def _update_app_status(self):
        """Update the application status per agent as well as update the
            operation
        """

        if self.reboot_required == CommonKeys.TRUE:
            update_agent_field(
                self.agent_id, AgentKey.NeedsReboot,
                CommonKeys.YES, self.username
            )

        if self.success == CommonKeys.TRUE or self.success == CommonKeys.FALSE:
            if (self.success == CommonKeys.TRUE and
                    re.search(r'^install', self.oper_type)):

                status = CommonAppKeys.INSTALLED
                install_date = self.date_now

            elif (self.success == CommonKeys.TRUE and
                    re.search(r'^uninstall', self.oper_type)):

                status = CommonAppKeys.AVAILABLE
                install_date = self.begining_of_time

            elif (self.success == CommonKeys.FALSE and
                    re.search(r'^install', self.oper_type)):

                status = CommonAppKeys.AVAILABLE
                install_date = self.begining_of_time

            elif (self.success == CommonKeys.FALSE and
                    re.search(r'^uninstall', self.oper_type)):

                status = CommonAppKeys.INSTALLED
                install_date = self.begining_of_time


            data_to_update = (
                {
                    SharedAppKeys.Status: status,
                    SharedAppKeys.InstallDate: install_date
                }
            )
            app_exist = get_app_data(self.app_id, table=self.CurrentAppsCollection)

            if app_exist:
                if (oper_type == AgentOperations.INSTALL_OS_APPS or
                        oper_type == AgentOperations.UNINSTALL):

                    update_os_app_per_agent(self.agent_id, self.app_id, data_to_update)

                elif oper_type == AgentOperations.INSTALL_CUSTOM_APPS:
                    update_custom_app_per_agent(self.agent_id, self.app_id, data_to_update)

                elif oper_type == AgentOperations.INSTALL_SUPPORTED_APPS:
                    update_supported_app_per_agent(self.agent_id, self.app_id, data_to_update)

                elif oper_type == AgentOperations.INSTALL_AGENT_APPS:
                    update_agent_app_per_agent(self.agent_id, self.app_id, data_to_update)

            oper_app_exists = (
                operation_for_agent_and_app_exist(
                    self.operation_id, self.agent_id, self.app_id
                )
            )

            if oper_app_exists:
                if self.success == CommonKeys.TRUE:
                    status_code = AgentOperationCodes.ResultsReceived

                    if self.apps_to_delete:
                        self._apps_to_delete()

                    if self.apps_to_add:
                        self._apps_to_add()

                elif self.success == CommonKeys.FALSE:
                    status_code = AgentOperationCodes.ResultsReceivedWithErrors

                operation_updated = (
                    self.patching_operation.update_app_results(
                        self.operation_id, self.agent_id,
                        self.app_id, status_code,
                        errors=self.error
                    )
                )
                if operation_updated:
                    msg = 'Results updated'
                    results[ApiResultKeys.GENERIC_STATUS_CODE] = (
                        GenericCodes.ObjectUpdated
                    )

                    results[ApiResultKeys.VFENSE_STATUS_CODE] = (
                        AgentResultCodes.ResultsUpdated
                    )

                    results[ApiResultKeys.MESSAGE] = msg

                else:
                    msg = 'Results failed to update'
                    results[ApiResultKeys.GENERIC_STATUS_CODE] = (
                        GenericFailureCodes.FailedToUpdateObject
                    )

                    results[ApiResultKeys.VFENSE_STATUS_CODE] = (
                        AgentFailureResultCodes.ResultsFailedToUpdate
                    )

                    results[ApiResultKeys.MESSAGE] = msg

            else:
                msg = 'Invalid operation id'
                results[ApiResultKeys.GENERIC_STATUS_CODE] = (
                    GenericFailureCodes.InvalidId
                )

                results[ApiResultKeys.VFENSE_STATUS_CODE] = (
                    AgentFailureResultCodes.InvalidOperationId
                )

                results[ApiResultKeys.MESSAGE] = msg

        else:
            msg = 'Invalid success value'
            results[ApiResultKeys.GENERIC_STATUS_CODE] = (
                GenericFailureCodes.FailedToUpdateObject
            )

            results[ApiResultKeys.VFENSE_STATUS_CODE] = (
                AgentFailureResultCodes.InvalidSuccessValue
            )

            results[ApiResultKeys.MESSAGE] = msg

        return(results)