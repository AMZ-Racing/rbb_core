# AMZ-Driverless
#  Copyright (c) 2022 Authors:
#   - Adrian Brandemuehl <abrandemuehl@gmail.com>
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

from datetime import datetime
from typing import Tuple, List, Any

import connexion
import rbb_server.helper.auth as auth
import rbb_server.helper.database as db_helper
from flask import redirect, Response
from rbb_server.helper.error import handle_exception
from sqlalchemy import and_
from sqlalchemy.orm.query import Query
from sqlalchemy.orm import scoped_session

from rbb_server.helper.permissions import Permissions
from rbb_server.model.database import Database
from rbb_server.model.datafile_store import DataFileStore
from rbb_server.model.datafile_store import DataFile
from rbb_server.model.tag import Tag
from rbb_server.model.datafile_comment import DataFileComment
from rbb_server.model.task import Task, TaskState
from rbb_server.helper.storage import Storage
from rbb_swagger_server.models.datafile_detailed import DataFileDetailed
from rbb_swagger_server.models.comment import Comment
from rbb_swagger_server.models.error import Error
from rbb_swagger_server.models.tag import Tag as SwaggerTag


def find_datafile_in_database(session: scoped_session, store_name: str, datafile_name: str) -> Tuple[Union[Query,None], Union[Error, None]]:
    q = session.query(DataFileStore).filter(DataFileStore.name == store_name)
    if q.count() == 0:
        return None, Error(code=404, message="Store not found")
    store = q[0]

    q = session.query(DataFile).filter(
        and_(DataFile.store_id == store.uid, DataFile.name == datafile_name)
    )  # type: Query

    if q.count() == 0:
        return None, Error(code=404, message="DataFile not found")

    return q[0], None


@auth.requires_auth_with_permission(Permissions.DataFileWrite)
def put_tag(tag: DataFileTag, tag_obj: SwaggerTag, user: Union[User, None]=None) -> Union[SwaggerTag, Error]:
    """Create/update tag

     # noqa: E501

    :param tag: Name of the tag
    :type tag: str
    :param tag_obj: Tag information
    :type tag_obj: dict | bytes

    :rtype: Tag
    """
    tag = tag.strip().lower()

    if connexion.request.is_json:
        tag_obj = SwaggerTag.from_dict(connexion.request.get_json())

    # We do allow renaming tags
    # if tag_obj.tag != tag:
    #     return Error(code=400, message="Path and body tag are not the same"), 400

    try:
        session = Database.get_session()
        q = session.query(Tag).filter(Tag.tag == tag)  # type: Query

        model = Tag()
        if q.count() == 1:
            model = q.first()
        else:
            if tag_obj.tag != tag:
                return Error(code=400, message="Path and body tag have to be equal for a new tag"), 400
            session.add(model)

        model.from_swagger_model(tag_obj)
        session.commit()

        return model.to_swagger_model(user=user)

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.DataFileWrite)
def put_datafile_tags(store_name: str, datafile_name: str, tags: list[str], auto_create: bool=False, user: Union[User, None]=None) -> Union[list[Tag], Error]:
    """Change datafile tags

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str
    :param datafile_name: Name of the datafile
    :type datafile_name: str
    :param tags: List of tags
    :type tags: List[]
    :param auto_create: Create non existing tags
    :type auto_create: bool

    :rtype: List[Tag]
    """
    try:
        session = Database.get_session()
        datafile, e = find_datafile_in_database(session, store_name, datafile_name)
        if e:
            return e, e.code

        tag_models = []

        tags_unique = list(set([x.strip().lower() for x in tags]))
        for tag in tags_unique:
            q = session.query(Tag).filter(Tag.tag == tag)  # type: Query
            if q.count() == 1:
                tag_models.append(q.first())
            else:
                if auto_create:
                    tag_models.append(Tag(tag=tag, color=""))
                else:
                    return Error(code=400, message="Tag '" + tag + "' does not exist"), 400

        datafile.tags = tag_models
        session.commit()

        return get_datafile_tags(store_name, datafile_name)

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.DataFileRead)
def list_tags(user: Union[User, None]=None) -> Union[list[SwaggerTag], Error]:
    """List all tags

     # noqa: E501


    :rtype: List[Tag]
    """
    try:
        session = Database.get_session()
        q = session.query(Tag) #type: Query
        return [p.to_swagger_model(user=user) for p in q]

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.DataFileRead)
def get_tag(tag: str, user: Union[User, None]=None)-> Union[SwaggerTag, Error]:
    """Get tag info

     # noqa: E501

    :param tag: Name of the tag
    :type tag: str

    :rtype: Tag
    """
    try:
        session = Database.get_session()
        q = session.query(Tag).filter(Tag.tag == tag)  # type: Query

        if q.count() == 0:
            return Error(code=404, message="Tag not found"), 404

        return q[0].to_swagger_model(user=user)

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.DataFileRead)
def get_datafile_tags(store_name:str, datafile_name:str, user: Union[User, None]=None) -> Union[list[Tag], Error]:
    """List tag from datafile

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str
    :param datafile_name: Name of the datafile
    :type datafile_name: str

    :rtype: List[Tag]
    """
    try:
        session = Database.get_session()
        datafile_model, e = find_datafile_in_database(session, store_name, datafile_name)
        if e:
            return e, e.code

        return [p.to_swagger_model(user=user) for p in datafile_model.tags]

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.DataFileWrite)
def patch_datafile_meta(store_name:str, datafile_name:str, datafile: DataFile, trigger:str="", user:Union[User,None]=None) -> Union[DataFileDetailed, Error]:  # noqa: E501
    """Partial update of datafile information (this only supports a few fields)

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str
    :param datafile_name: Name of the datafile
    :type datafile_name: str
    :param datafile: DataFile to register
    :type datafile: dict | bytes

    :rtype: DataFileDetailed
    """
    if connexion.request.is_json:
        datafile = connexion.request.get_json()

    try:
        session = Database.get_session()
        datafile_model, e = find_datafile_in_database(session, store_name, datafile_name)
        if e:
            return e, e.code

        changed = False

        if 'comment' in datafile and isinstance(datafile['comment'], str):
            datafile_model.comment = datafile['comment']
            changed = True

        if 'in_trash' in datafile:
            datafile_model.in_trash = datafile['in_trash']
            changed = True

        if changed:
            session.commit()

        return datafile_model.to_swagger_model_detailed(user=user)

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.DataFileRead)
def get_datafile_meta(store_name:str, datafile_name:str, user:Union[User,None]=None) -> DataFileDetailed:
    """
    List products from datafile

    :param store_name: Name of the store
    :type store_name: str
    :param datafile_name: Name of the datafile
    :type datafile_name: str

    :rtype: DataFileDetailed
    """
    try:
        session = Database.get_session()
        datafile_model, e = find_datafile_in_database(session, store_name, datafile_name)
        if e:
            return e, e.code

        return datafile_model.to_swagger_model_detailed(user=user)

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.DataFileRead)
def get_datafile_file(store_name:str, datafile_name:str, user:Union[User,None]=None)-> Union[Response, Error]:
    """
    Get datafile

    :param store_name: Name of the store
    :type store_name: str
    :param datafile_name: Name of the datafile
    :type datafile_name: str

    :rtype: Binary
    """
    try:
        session = Database.get_session()
        q = session.query(DataFileStore).filter(DataFileStore.name == store_name)  # type: Query
        if q.count() == 0:
            return Error(code=404, message="Store not found"), 404
        store = q[0]

        q = session.query(DataFile).filter(
            and_(DataFile.store_id == store.uid, DataFile.name == datafile_name)
        )  # type: Query

        if q.count() == 0:
            return Error(code=404, message="DataFile not found"), 404
        datafile = q[0]

        # TODO: SOME MORE ROBUST ERROR HANDLING

        storage_plugin = Storage.factory(store.name, store.store_type, store.store_data)
        link = storage_plugin.download_link(datafile.store_data)

        return redirect(link, code=302)

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.DataFileRead)
def list_datafiles(store_name, limit:int=0, offset:int=0, ordering:str="desc",
        discovered_gte:Union[str,None]=None,
        discovered_lte:Union[str,None]=None,
        meta_available:Union[bool,None]=None, name:Union[str, None]=None,
        tags:Union[str,None]=None, in_trash:Union[bool,None]=None,
        user:Union[User,None]=None) -> Union[List[DataFileSummary],Error]:
    """
    List datafiles in store based on filters

    :param store_name: Name of the store
    :param limit: Maximum number of entries to return
    :param offset: How many entries to skip.
    :param ordering: Order of the results. "asc" or "desc"
    :param discovered_gte: Filter for discovered time
    :param discovered_lte: Filter for discovered time
    :param meta_available: Filter for meta_available
    :param name: Filter for name
    :param

    :rtype: List[DataFileSummary]
    """

    if in_trash is None:
        in_trash = False

    try:
        session = Database.get_session()
        q = session.query(DataFileStore).filter(DataFileStore.name == store_name) #type: Query
        if q.count() == 0:
            return Error(code=404, message="Store not found"), 404

        q = session.query(DataFile).filter(DataFile.store_id == q[0].uid) #type: Query

        q = db_helper.filter_datetime_lte(q, discovered_lte, DataFile.discovered)
        q = db_helper.filter_datetime_gte(q, discovered_gte, DataFile.discovered)

        q = db_helper.filter_datetime_lte(q, start_time_lte, DataFile.start_time)
        q = db_helper.filter_datetime_gte(q, start_time_gte, DataFile.start_time)

        q = db_helper.filter_datetime_lte(q, end_time_lte, DataFile.end_time)
        q = db_helper.filter_datetime_gte(q, end_time_gte, DataFile.end_time)

        q = db_helper.filter_boolean_eq(q, meta_available, DataFile.meta_available)
        q = db_helper.filter_boolean_eq(q, is_extracted, DataFile.is_extracted)
        q = db_helper.filter_boolean_eq(q, in_trash, DataFile.in_trash)
        q = db_helper.filter_number_gte(q, duration_gte, DataFile.duration)
        q = db_helper.filter_number_lte(q, duration_lte, DataFile.duration)
        q = db_helper.filter_string(q, name, DataFile.name)

        # Not so efficient but for now good enough tag filtering
        if tags:
            tags = [x.strip() for x in tags.split(",") if x.strip()]
            for tag in tags:
                q = q.filter(DataFile.tags.any(Tag.tag == tag))

        q = db_helper.query_pagination_ordering(q, offset, limit, ordering, {
            'discovered': DataFile.discovered,
            'start_time': DataFile.start_time,
            'end_time': DataFile.end_time,
            'name': DataFile.name,
            'duration': DataFile.duration,
            'size': DataFile.size
        })

        return [p.to_swagger_model_summary(user=user) for p in q]

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.DataFileWrite)
def put_datafile_meta(store_name:str, datafile_name:str, datafile:DataFile, user:Union[User,None]=None) -> Union[DataFileDetailed, Error]:
    """
    Create/update datafile information

    :param store_name: Name of the store
    :type store_name: str
    :param datafile_name: Name of the datafile
    :type datafile_name: str
    :param datafile: DataFile to register
    :type datafile: dict | bytes

    :rtype: DataFileDetailed
    """
    if connexion.request.is_json:
        datafile = DataFileDetailed.from_dict(connexion.request.get_json())

    session = Database.get_session()
    new_datafile = False
    try:
        # Check the store
        q = session.query(DataFileStore).filter(DataFileStore.name == store_name) # type: Query
        if q.count() != 1:
            return Error(code=404, message="Store not found"), 404
        store = q.first()  # type: DataFileStore

        # Query existing datafile
        q = session.query(DataFile).filter(
            and_(DataFile.store_id == store.uid, DataFile.name == datafile_name)
        ) # type: Query

        # Create new datafile or use existing
        datafile_model = None
        if q.count() == 1:
            # Existing datafile
            datafile_model = q.first()
        else:
            datafile_model = DataFile()
            datafile_model.store = store
            new_datafile = True
            session.add(datafile_model)

        datafile_model.from_swagger_model(datafile, user=user)

        session.commit()

        q = session.query(DataFile).filter(
            and_(DataFileStore.uid == store.uid, DataFile.name == datafile_name)
        )
        fresh_model = q.first()

        return fresh_model.to_swagger_model_detailed(user), 200

    except Exception as e:
        session.rollback()
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.DataFileCommentWrite)
def new_datafile_comment(store_name:str, datafile_name:str, comment:DataFileComment, user:Union[User, None]=None) -> Union[Comment, Error]: # noqa: E501
    """Delete a comment

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str
    :param datafile_name: Name of the datafile
    :type datafile_name: str
    :param comment: Comment
    :type comment: dict | bytes

    :rtype: Comment
    """
    if connexion.request.is_json:
        comment = Comment.from_dict(connexion.request.get_json())  # noqa: E501

    try:
        session = Database.get_session()
        datafile, e = find_datafile_in_database(session, store_name, datafile_name)
        if e:
            return e, e.code

        comment_model = DataFileComment()
        comment_model.from_swagger_model(comment)
        comment_model.user_id = user.uid
        comment_model.datafile_id = datafile.uid

        session.add(comment_model)
        session.commit()

        return comment_model.to_swagger_model()

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.DataFileCommentWrite)
def delete_datafile_comment(store_name:str, datafile_name:str, comment_id:int, user:Union[User,None]=None) -> Union[Any, Error]:  # noqa: E501
    """Post a comment

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str
    :param datafile_name: Name of the datafile
    :type datafile_name: str
    :param comment_id: Comment identifier
    :type comment_id: int

    :rtype: None
    """
    try:
        session = Database.get_session()
        datafile, e = find_datafile_in_database(session, store_name, datafile_name)
        if e:
            return e, e.code

        q = session.query(DataFileComment).filter(DataFileComment.uid == comment_id) # type: Query
        if q.count() != 1 or q.first().datafile_id != datafile.uid:
            return Error(code=404, message="Comment not found"), 404

        session.delete(q.first())
        session.commit()

        return "", 204

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.DataFileCommentRead)
def get_datafile_comments(store_name: str, datafile_name: str, user:[User, None]=None) -> Union[List[Comment], Error]:  # noqa: E501
    """List comments from datafile

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str
    :param datafile_name: Name of the datafile
    :type datafile_name: str

    :rtype: List[Comment]
    """
    try:
        session = Database.get_session()
        datafile, e = find_datafile_in_database(session, store_name, datafile_name)
        if e:
            return e, e.code

        return [p.to_swagger_model(user=user) for p in datafile.comments]

    except Exception as e:
        return handle_exception(e)
