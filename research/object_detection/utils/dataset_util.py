# Copyright 2017 The TensorFlow Authors. All Rights Reserved.
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
# ==============================================================================

import tensorflow as tf


def int64_feature(value):
  return tf.train.Feature(int64_list=tf.train.Int64List(value=[value]))


def int64_list_feature(value):
  return tf.train.Feature(int64_list=tf.train.Int64List(value=value))


def bytes_feature(value):
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=[value]))


def bytes_list_feature(value):
  return tf.train.Feature(bytes_list=tf.train.BytesList(value=value))


def float_list_feature(value):
  return tf.train.Feature(float_list=tf.train.FloatList(value=value))


def read_examples_list(path):
  with tf.gfile.GFile(path) as fid:
    lines = fid.readlines()
  return [line.strip().split(' ')[0] for line in lines]


def recursive_parse_xml_to_dict(xml):
  if not xml:
    return {xml.tag: xml.text}
  result = {}
  for child in xml:
    child_result = recursive_parse_xml_to_dict(child)
    if child.tag != 'object':
      result[child.tag] = child_result[child.tag]
    else:
      if child.tag not in result:
        result[child.tag] = []
      result[child.tag].append(child_result[child.tag])
  return {xml.tag: result}


def make_initializable_iterator(dataset):
  iterator = dataset.make_initializable_iterator()
  tf.add_to_collection(tf.GraphKeys.TABLE_INITIALIZERS, iterator.initializer)
  return iterator


def read_dataset(
    file_read_func, decode_func, input_files, config, num_workers=1,
    worker_index=0):
  filenames = tf.concat([tf.matching_files(pattern) for pattern in input_files],
                        0)
  dataset = tf.data.Dataset.from_tensor_slices(filenames)
  dataset = dataset.shard(num_workers, worker_index)
  dataset = dataset.repeat(config.num_epochs or None)
  if config.shuffle:
    dataset = dataset.shuffle(config.filenames_shuffle_buffer_size,
                              reshuffle_each_iteration=True)
  cycle_length = tf.cast(
      tf.minimum(config.num_readers, tf.size(filenames)), tf.int64)
  dataset = dataset.interleave(
      file_read_func, cycle_length=cycle_length, block_length=1)

  if config.shuffle:
    dataset = dataset.shuffle(config.shuffle_buffer_size,
                              reshuffle_each_iteration=True)

  dataset = dataset.map(decode_func, num_parallel_calls=config.num_readers)
  return dataset.prefetch(config.prefetch_buffer_size)
