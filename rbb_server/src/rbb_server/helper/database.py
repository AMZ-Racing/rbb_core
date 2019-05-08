# AMZ-Driverless
#  Copyright (c) 2019 Authors:
#   - Huub Hendrikx <hhendrik@ethz.ch>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from rbb_swagger_server import util


class UnknownColumn(RuntimeError):
    def __init__(self):
        super(UnknownColumn, self).__init__("Unknown column in ordering")


class UnknownOrdering(RuntimeError):
    def __init__(self):
        super(UnknownOrdering, self).__init__("Unknown ordering")


def filter_datetime_gte(q, input_field, column):
    if input_field is not None:
        input_field = util.deserialize_datetime(input_field)
        return q.filter(column >= input_field)
    else:
        return q


def filter_datetime_lte(q, input_field, column):
    if input_field is not None:
        input_field = util.deserialize_datetime(input_field)
        return q.filter(column <= input_field)
    else:
        return q


def filter_number_lte(q, input_field, column):
    if input_field is not None:
        return q.filter(column <= input_field)
    else:
        return q


def filter_number_gte(q, input_field, column):
    if input_field is not None:
        return q.filter(column >= input_field)
    else:
        return q


def filter_boolean_eq(q, input_field, column):
    if input_field is not None:
        return q.filter(column == input_field)
    else:
        return q


def filter_string(q, input_field, column):
    if input_field is not None:
        return q.filter(column.ilike(input_field))
    else:
        return q


def query_pagination_ordering(q, offset=None, limit=None, ordering=None, column_mapping=None):

    if ordering and column_mapping is not None:
        ordering = [pair.split(":") for pair in ordering.split(",")]

        for pair in ordering:
            column_name = pair[0].rstrip()
            order = pair[1].rstrip()

            if column_name not in column_mapping:
                raise UnknownColumn()

            column = column_mapping[column_name]

            if order == "asc":
                q = q.order_by(column.asc())
            elif order == "desc":
                q = q.order_by(column.desc())
            else:
                raise UnknownOrdering()

    if offset is not None:
        q = q.offset(offset)

    if limit is not None:
        q = q.limit(limit)

    return q