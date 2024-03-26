# -*- coding: utf-8 -*-
#  Copyright (c) 2020 - 2023 Ricardo Bartels. All rights reserved.
#
#  netbox-sync.py
#
#  This work is licensed under the terms of the MIT license.
#  For a copy, see file LICENSE.txt included in this
#  repository or visit: <https://opensource.org/licenses/MIT>.

from module.common.logging import get_logger
import re

log = get_logger()


class ExcludedVLAN:
    """
    initializes and verifies if an VLAN should be excluded from being synced to NetBox
    """

    def __init__(self, vlan):
        self._validation_failed = False

        self.site = None

        if vlan is None:
            self._validation_failed = True
            log.error("submitted VLAN string for VLAN exclusion was 'None'")
            return

        vlan_split = [x.replace('\\', "") for x in re.split(r'(?<!\\)/', vlan)]

        if len(vlan_split) == 1:
            self._value = vlan_split[0]
        elif len(vlan_split) == 2:
            self.site = vlan_split[0]
            self._value = vlan_split[1]
        else:
            self._validation_failed = True
            log.error("submitted VLAN string for VLAN exclusion contains name or site including '/'. " +
                      "A '/' which belongs to the name needs to be escaped like '\\/'.")

    def site_matches(self, site_name):

        if self.site is None:
            return True

        # string or regex matches
        try:
            if ([self.site, site_name]).count(None) == 0 and re.search(f"^{self.site}$", site_name):
                log.debug2(f"VLAN exclude site name '{site_name}' matches '{self.site}'")
                return True
        except Exception:
            return False

        return False

    def is_valid(self):

        return not self._validation_failed


class ExcludedVLANName(ExcludedVLAN):

    def __init__(self, vlan):

        super().__init__(vlan)

        self.name = None

        if self._validation_failed is True:
            return

        self.name = self._value

    def matches(self, name, site=None):

        if self.site_matches(site) is False:
            return False

        # string or regex matches
        try:
            if ([self.name, name]).count(None) == 0 and re.search(f"^{self.name}$", name):
                log.debug2(f"VLAN exclude name '{name}' matches '{self.name}'")
                return True
        except Exception as e:
            log.warning(f"Unable to match exclude VLAN name '{name}' to '{self.name}': {e}")
            return False

        return False


class ExcludedVLANID(ExcludedVLAN):

    def __init__(self, vlan):

        super().__init__(vlan)

        self.range = None

        if self._validation_failed is True:
            return

        try:
            if "-" in self._value and int(self._value.split("-")[0]) >= int(self._value.split("-")[1]):
                log.error(f"range has to start with the lower id: {self._value}")
                self._validation_failed = True
                return

            self.range = sum(
                ((list(range(*[int(j) + k for k, j in enumerate(i.split('-'))])) if '-' in i else [int(i)])
                 for i in self._value.split(',')), []
            )
        except Exception as e:
            log.error(f"unable to extract ids from value '{self._value}': {e}")
            self._validation_failed = True

    def matches(self, vlan_id, site=None):

        if self.site_matches(site) is False:
            return False

        try:
            if int(vlan_id) in self.range:
                log.debug2(f"VLAN exclude id '{vlan_id}' matches '{self._value}'")
                return True
        except Exception as e:
            log.warning(f"Unable to match exclude VLAN id '{vlan_id}' to '{self._value}': {e}")
            return False

        return False


