# Copyright 2014 Diamond Light Source Ltd.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
.. module:: data_with_darks_and_flats
   :platform: Unix
   :synopsis: A class for loading data that has associated dark and flat \
       fields.

.. moduleauthor:: Nicola Wadeson <scientificsoftware@diamond.ac.uk>

"""

import numpy as np
import copy

from savu.data.data_structures.data_types.base_type import BaseType


class DataWithDarksAndFlats(BaseType):

    def __init__(self, data_obj, proj_dim, image_key):
        self.data_obj = data_obj
        self.fscale = 1
        self.dscale = 1
        self.flat_updated = False
        self.dark_updated = False
        self.image_key = image_key
        self.data = data_obj.data
        self.proj_dim = proj_dim
        self.dark_flat_slice_list = None

    def _copy_base(self, new_obj):
        new_obj.flat_updated = self.flat_updated
        new_obj.dark_updated = self.dark_updated
        self._set_dark_and_flat()

    def get_image_key(self):
        return self.image_key

    def _get_image_key_data_shape(self):
        data_idx = self.get_index(0)
        new_shape = list(self.data.shape)
        new_shape[self.proj_dim] = len(data_idx)
        return tuple(new_shape)

    def _getitem_imagekey(self, idx):
        index = list(idx)
        index[self.proj_dim] = \
            self.get_index(0, full=True)[idx[self.proj_dim]].tolist()
        return self.data[tuple(index)]

    def _getitem_noimagekey(self, idx):
        return self.data[idx]

    def __setitem__(self, key, val):
        self.data[key] = val

    def get_dark_flat_slice_list(self):
        slice_list = self.data_obj._preview._get_preview_slice_list()
        remove_dim = self.data_obj.find_axis_label_dimension('rotation_angle')
        slice_list[remove_dim] = slice(None)

        if len(slice_list) > 3:
            idx = np.arange(0, len(slice_list))
            detX = self.data_obj.find_axis_label_dimension('detector_x')
            detY = self.data_obj.find_axis_label_dimension('detector_y')
            remove = set(idx).difference(set([remove_dim, detX, detY]))
            for dim in sorted(list(remove), reverse=True):
                del slice_list[dim]

        return slice_list

    def _set_scale(self, name, scale):
        self.set_flat_scale(scale) if name is 'flat' else\
            self.set_dark_scale(scale)

    def set_flat_scale(self, fscale):
        self.fscale = float(fscale)

    def set_dark_scale(self, dscale):
        self.dscale = float(dscale)

    def get_shape(self):
        return self.shape

    def dark_mean(self):
        """ Get the averaged dark projection data. """
        return self._calc_mean(self.dark())

    def flat_mean(self):
        """ Get the averaged flat projection data. """
        return self._calc_mean(self.flat())

    def _calc_mean(self, data):
        return data if len(data.shape) is 2 else\
            data.mean(self.proj_dim).astype(np.float32)

    def get_index(self, key, full=False):
        """ Get the projection index of a specific image key value.

        :params int key: the image key value
        """
        if full is True:
            return np.where(self.image_key == key)[0]
        else:
            return self.__get_preview_index(key)

    def __get_preview_index(self, key):
        try:
            # amend if there is previewing
            slice_list = self.data_obj.get_preview().\
                _get_preview_slice_list()[self.proj_dim]
            return self.__get_reduced_index(key, slice_list)
        except:
            return np.where(self.image_key == key)[0]

    def __get_reduced_index(self, key, slice_list):
        """ Get the projection index of a specific image key value when\
            previewing has been applied. """
        data_entries = np.where(self.image_key == 0)[0][slice_list]
        if key == 0:
            return data_entries

        index = np.where(self.image_key == key)[0]
        start_idx, end_idx, start_entry, end_entry = \
            self.__get_start_end_idx(index)

        val = index[np.where(np.less(index, data_entries[0]))[0][-1]]
        start = start_idx[np.where(end_entry == val)[0]]
        val2 = index[np.where(np.greater(index, data_entries[-1]))[0][0]]
        end = end_idx[np.where(end_entry == val2)[0]]+1

        return index[start:end]

    def _get_start_end_idx(self, index):
        start = [0] + list(np.where(np.diff(index) > 1)[0]+1)
        end = np.array(start[1:] + [len(index)])-1
        start_entry = index[start]
        end_entry = index[end]
        return start, end, start_entry, end_entry

    def __get_data(self, key):
        index = [slice(None)]*self.nDims
        index[self.proj_dim] = self.get_index(key)
        data = self.data[tuple(index)]

        sl = list(copy.deepcopy(self.dark_flat_slice_list))
        if len(data.shape) is 2:
            rot_dim = self.data_obj.find_axis_label_dimension('rotation_angle')
            del sl[rot_dim]

        return data[sl]

    def dark_image_key_data(self):
        """ Get the dark data. """
        return self.__get_data(2)*self.dscale

    def flat_image_key_data(self):
        """ Get the flat data. """
        return self.__get_data(1)*self.fscale

    def update_dark(self, data):
        self.dark_updated = data
        self.dscale = 1
        self.data_obj.meta_data.set_meta_data('dark', self._calc_mean(data))

    def update_flat(self, data):
        self.flat_updated = data
        self.fscale = 1
        self.data_obj.meta_data.set_meta_data('flat', self._calc_mean(data))


class ImageKey(DataWithDarksAndFlats):
    """ This class is used to get data from a dataset with an image key. """

    def __init__(self, data_obj, image_key, proj_dim, ignore=None):
        super(ImageKey, self).__init__(data_obj, proj_dim, image_key)
        self.shape = self._get_image_key_data_shape()
        self.nDims = len(self.shape)
        self._getitem = self._getitem_imagekey
        if ignore:
            self.__ignore_image_key_entries(ignore)

    def __getitem__(self, idx):
        return self._getitem(idx)

    def _copy(self, new_obj):
        self._copy_base(new_obj)

    def __ignore_image_key_entries(self, ignore):
        a, a, start, end = self._get_start_end_idx(self.get_index(1))
        if not isinstance(ignore, list):
            ignore = [ignore]
        for batch in ignore:
            self.image_key[start[batch-1]:end[batch-1]+1] = 3

    def dark(self):
        """ Get the dark data. """
        return self.dark_updated if self.dark_updated else\
            self.dark_image_key_data()

    def flat(self):
        """ Get the flat data. """
        return self.flat_updated if self.flat_updated else\
            self.flat_image_key_data()

    def _set_dark_and_flat(self):
        self.dark_flat_slice_list = tuple(self.get_dark_flat_slice_list())
        if len(self.get_index(2)):
            self.data_obj.meta_data.set_meta_data('dark', self.dark_mean())
        if len(self.get_index(1)):
            self.data_obj.meta_data.set_meta_data('flat', self.flat_mean())


class NoImageKey(DataWithDarksAndFlats):
    """ This class is used to get data from a dataset with separate darks and
        flats. """

    def __init__(self, data_obj, image_key, proj_dim):
        super(NoImageKey, self).__init__(data_obj, proj_dim, image_key)
        self.dark_path = None
        self.flat_path = None
        self.orig_image_key = copy.copy(image_key)
        self.flat_image_key = False
        self.dark_image_key = False
        if self.image_key is not None:
            self.shape = self._get_image_key_data_shape()
            self._getitem = self._getitem_imagekey
        else:
            self.shape = data_obj.data.shape
            self._getitem = self._getitem_noimagekey
        self.data_obj = data_obj
        self.nDims = len(self.shape)

    def __getitem__(self, idx):
        return self._getitem(idx)

    def _copy(self, new_obj):
        new_obj.dark_path = self.dark_path
        new_obj.flat_path = self.flat_path
        new_obj.flat_image_key = self.flat_image_key
        new_obj.dark_image_key = self.dark_image_key
        self._copy_base(new_obj)

    def _set_flat_path(self, path, imagekey=False):
        self.flat_image_key = imagekey
        self.flat_path = path

    def _set_dark_path(self, path, imagekey=False):
        self.dark_image_key = imagekey
        self.dark_path = path

    def get_shape(self):
        return self.shape

    def dark(self):
        """ Get the dark data. """
        if self.dark_updated:
            return self.dark_updated
        if self.dark_image_key is not False:
            self.image_key = self.dark_image_key
            dark = self.dark_image_key_data()
            self.image_key = self.orig_image_key
            return dark

        return self.dark_path[self.dark_flat_slice_list]*self.dscale

    def flat(self):
        """ Get the flat data. """
        if self.flat_updated:
            return self.flat_updated()
        if self.flat_image_key is not False:
            self.image_key = self.flat_image_key
            flat = self.flat_image_key_data()
            self.image_key = self.orig_image_key
            return flat
        return self.flat_path[self.dark_flat_slice_list]*self.fscale

    def _set_dark_and_flat(self):
        self.dark_flat_slice_list = self.get_dark_flat_slice_list()
        # remove extra dimension if 3d to 4d mapping
        from savu.data.data_structures.data_types.map_3dto4d_h5 \
            import Map3dto4dh5
        if Map3dto4dh5 in self.__class__.__bases__:
            del self.dark_flat_slice_list[-1]

#        if len(self.dark_flat_slice_list) < len(self.dark_path.shape):
            # change dimensions here

        self.dark_flat_slice_list = tuple(self.dark_flat_slice_list)
        self.data_obj.meta_data.set_meta_data('dark', self.dark_mean())
        self.data_obj.meta_data.set_meta_data('flat', self.flat_mean())
