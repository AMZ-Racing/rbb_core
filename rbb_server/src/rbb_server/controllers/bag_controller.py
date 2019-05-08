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

from datetime import datetime

import connexion
import rbb_server.helper.auth as auth
import rbb_server.helper.database as db_helper
from flask import redirect
from rbb_server.helper.error import handle_exception
from sqlalchemy import and_
from sqlalchemy.orm.query import Query

from rbb_server.helper.permissions import Permissions
from rbb_server.model.database import Database, RosbagStore, Rosbag, RosbagTopic, RosbagProduct, Tag
from rbb_server.model.rosbag_comment import RosbagComment
from rbb_server.model.task import Task, TaskState
from rbb_server.hooks.new_bag_hook import NewBagHook
from rbb_server.helper.storage import Storage
from rbb_swagger_server.models.bag_detailed import BagDetailed
from rbb_swagger_server.models.comment import Comment
from rbb_swagger_server.models.error import Error
from rbb_swagger_server.models.tag import Tag as SwaggerTag


def find_bag_in_database(session, store_name, bag_name):
    q = session.query(RosbagStore).filter(RosbagStore.name == store_name)  # type: Query
    if q.count() == 0:
        return None, Error(code=404, message="Store not found")
    store = q[0]

    q = session.query(Rosbag).filter(
        and_(Rosbag.store_id == store.uid, Rosbag.name == bag_name)
    )  # type: Query

    if q.count() == 0:
        return None, Error(code=404, message="Bag not found")

    return q[0], None


@auth.requires_auth_with_permission(Permissions.BagWrite)
def put_tag(tag, tag_obj, user=None):
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


@auth.requires_auth_with_permission(Permissions.BagWrite)
def put_bag_tags(store_name, bag_name, tags, auto_create=None, user=None):
    """Change bag tags

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str
    :param bag_name: Name of the bag
    :type bag_name: str
    :param tags: List of tags
    :type tags: List[]
    :param auto_create: Create non existing tags
    :type auto_create: bool

    :rtype: List[Tag]
    """
    try:
        session = Database.get_session()
        bag, e = find_bag_in_database(session, store_name, bag_name)
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

        bag.tags = tag_models
        session.commit()

        return get_bag_tags(store_name, bag_name)

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.BagRead)
def list_tags(user=None):
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


@auth.requires_auth_with_permission(Permissions.BagRead)
def get_tag(tag, user=None):
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


@auth.requires_auth_with_permission(Permissions.BagRead)
def get_bag_tags(store_name, bag_name, user=None):
    """List tag from bag

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str
    :param bag_name: Name of the bag
    :type bag_name: str

    :rtype: List[Tag]
    """
    try:
        session = Database.get_session()
        bag_model, e = find_bag_in_database(session, store_name, bag_name)
        if e:
            return e, e.code

        return [p.to_swagger_model(user=user) for p in bag_model.tags]

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.BagWrite)
def patch_bag_meta(store_name, bag_name, bag, trigger=None, user=None):  # noqa: E501
    """Partial update of bag information (this only supports a few fields)

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str
    :param bag_name: Name of the bag
    :type bag_name: str
    :param bag: Bag to register
    :type bag: dict | bytes
    :param trigger: Hooks to trigger
    :type trigger: str

    :rtype: BagDetailed
    """
    if connexion.request.is_json:
        bag = connexion.request.get_json()

    try:
        session = Database.get_session()
        bag_model, e = find_bag_in_database(session, store_name, bag_name)
        if e:
            return e, e.code

        changed = False

        if 'comment' in bag and isinstance(bag['comment'], str):
            bag_model.comment = bag['comment']
            changed = True

        if 'extraction_failure' in bag:
            bag_model.extraction_failure = bag['extraction_failure']
            changed = True

        if 'in_trash' in bag:
            bag_model.in_trash = bag['in_trash']
            changed = True

        if changed:
            session.commit()

        return bag_model.to_swagger_model_detailed(user=user)

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.BagRead)
def get_bag_meta(store_name, bag_name, user=None):
    """
    List products from bag
    
    :param store_name: Name of the store
    :type store_name: str
    :param bag_name: Name of the bag
    :type bag_name: str

    :rtype: BagDetailed
    """
    try:
        session = Database.get_session()
        bag_model, e = find_bag_in_database(session, store_name, bag_name)
        if e:
            return e, e.code

        return bag_model.to_swagger_model_detailed(user=user)

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.BagRead)
def get_bag_file(store_name, bag_name, user=None):
    """
    Get rosbag
    
    :param store_name: Name of the store
    :type store_name: str
    :param bag_name: Name of the bag
    :type bag_name: str

    :rtype: Binary
    """
    try:
        session = Database.get_session()
        q = session.query(RosbagStore).filter(RosbagStore.name == store_name)  # type: Query
        if q.count() == 0:
            return Error(code=404, message="Store not found"), 404
        store = q[0]

        q = session.query(Rosbag).filter(
            and_(Rosbag.store_id == store.uid, Rosbag.name == bag_name)
        )  # type: Query

        if q.count() == 0:
            return Error(code=404, message="Bag not found"), 404
        bag = q[0]

        # TODO: SOME MORE ROBUST ERROR HANDLING

        storage_plugin = Storage.factory(store.name, store.store_type, store.store_data)
        link = storage_plugin.download_link(bag.store_data)

        return redirect(link, code=302)

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.BagRead)
def list_bags(store_name, limit=None, offset=None, ordering=None, discovered_gte=None, discovered_lte=None, start_time_gte=None,
              start_time_lte=None, end_time_gte=None, end_time_lte=None, duration_gte=None, duration_lte=None,
              meta_available=None, is_extracted=None, name=None, tags=None, in_trash=None, user=None):
    """
    List bags in store
    
    :param store_name: Name of the store
    :type store_name: str

    :rtype: List[BagSummary]
    """

    if in_trash is None:
        in_trash = False

    try:
        session = Database.get_session()
        q = session.query(RosbagStore).filter(RosbagStore.name == store_name) #type: Query
        if q.count() == 0:
            return Error(code=404, message="Store not found"), 404

        q = session.query(Rosbag).filter(Rosbag.store_id == q[0].uid) #type: Query

        q = db_helper.filter_datetime_lte(q, discovered_lte, Rosbag.discovered)
        q = db_helper.filter_datetime_gte(q, discovered_gte, Rosbag.discovered)

        q = db_helper.filter_datetime_lte(q, start_time_lte, Rosbag.start_time)
        q = db_helper.filter_datetime_gte(q, start_time_gte, Rosbag.start_time)

        q = db_helper.filter_datetime_lte(q, end_time_lte, Rosbag.end_time)
        q = db_helper.filter_datetime_gte(q, end_time_gte, Rosbag.end_time)

        q = db_helper.filter_boolean_eq(q, meta_available, Rosbag.meta_available)
        q = db_helper.filter_boolean_eq(q, is_extracted, Rosbag.is_extracted)
        q = db_helper.filter_boolean_eq(q, in_trash, Rosbag.in_trash)
        q = db_helper.filter_number_gte(q, duration_gte, Rosbag.duration)
        q = db_helper.filter_number_lte(q, duration_lte, Rosbag.duration)
        q = db_helper.filter_string(q, name, Rosbag.name)

        # Not so efficient but for now good enough tag filtering
        if tags:
            tags = [x.strip() for x in tags.split(",") if x.strip()]
            for tag in tags:
                q = q.filter(Rosbag.tags.any(Tag.tag == tag))

        q = db_helper.query_pagination_ordering(q, offset, limit, ordering, {
            'discovered': Rosbag.discovered,
            'start_time': Rosbag.start_time,
            'end_time': Rosbag.end_time,
            'name': Rosbag.name,
            'duration': Rosbag.duration,
            'size': Rosbag.size
        })

        return [p.to_swagger_model_summary(user=user) for p in q]

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.BagWrite)
def put_bag_meta(store_name, bag_name, bag, trigger=None, user=None):
    """
    Create/update bag information
    
    :param store_name: Name of the store
    :type store_name: str
    :param bag_name: Name of the bag
    :type bag_name: str
    :param bag: Bag to register
    :type bag: dict | bytes

    :rtype: BagDetailed
    """
    if connexion.request.is_json:
        bag = BagDetailed.from_dict(connexion.request.get_json())

    session = Database.get_session()
    new_bag = False
    try:
        # Check the store
        q = session.query(RosbagStore).filter(RosbagStore.name == store_name) # type: Query
        if q.count() != 1:
            return Error(code=404, message="Store not found"), 404
        store = q.first()  # type: RosbagStore

        # Query existing bag
        q = session.query(Rosbag).filter(
            and_(Rosbag.store_id == store.uid, Rosbag.name == bag_name)
        ) # type: Query

        # Create new bag or use existing
        bag_model = None
        if q.count() == 1:
            # Existing bag
            bag_model = q.first()
        else:
            bag_model = Rosbag()
            bag_model.store = store
            new_bag = True
            session.add(bag_model)

        bag_model.from_swagger_model(bag, user=user)

        ## Sync topics

        request_topics = {}
        for topic in bag.topics:
            request_topics[topic.name] = topic

        # Delete stale topics
        bag_model.topics[:] = [t for t in bag_model.topics if t.name in request_topics]

        # Update existing topics
        for topic in bag_model.topics:
            topic.from_swagger_model(request_topics[topic.name])
            del request_topics[topic.name]

        # Create new topics products
        for topic in request_topics:
            model = RosbagTopic().from_swagger_model(request_topics[topic])
            bag_model.topics.append(model)

        ## Sync products

        existing_request_products = {}
        new_request_products = []
        for product in bag.products:
            if product.uid:
                existing_request_products[int(product.uid)] = product
            else:
                new_request_products.append(product)

        # Delete stale products
        bag_model.products[:] = [p for p in bag_model.products if p.uid in existing_request_products]

        # Update existing products
        for product in bag_model.products:
            product.from_swagger_model(existing_request_products[product.uid])
            try:
                product.topic_mapping_from_swagger_model(existing_request_products[product.uid], bag_model.topics)
            except ValueError as e:
                return Error(code=500, message="Topics in product are not all in the bag"), 500

            try:
                product.file_mapping_from_swagger_model(existing_request_products[product.uid], session)
            except ValueError as e:
                return Error(code=500, message="Files in product are not all available"), 500

        # Create new products
        for request_product in new_request_products:
            product = RosbagProduct().from_swagger_model(request_product)
            bag_model.products.append(product)
            try:
                product.topic_mapping_from_swagger_model(request_product, bag_model.topics)
            except ValueError as e:
                return Error(code=500, message="Topics in new product are not all in the bag (%s)" % str(e)), 500

            try:
                product.file_mapping_from_swagger_model(request_product, session)
            except ValueError as e:
                return Error(code=500, message="Files in new product are not all available"), 500

        session.commit()

        q = session.query(Rosbag).filter(
            and_(RosbagStore.uid == store.uid, Rosbag.name == bag_name)
        )
        fresh_model = q.first()

        if new_bag:
            fresh_model = NewBagHook.trigger(fresh_model, store_name, session, trigger, user)

        return fresh_model.to_swagger_model_detailed(user), 200

    except Exception as e:
        session.rollback()
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.BagCommentWrite)
def new_bag_comment(store_name, bag_name, comment, user=None):  # noqa: E501
    """Delete a comment

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str
    :param bag_name: Name of the bag
    :type bag_name: str
    :param comment: Comment
    :type comment: dict | bytes

    :rtype: Comment
    """
    if connexion.request.is_json:
        comment = Comment.from_dict(connexion.request.get_json())  # noqa: E501

    try:
        session = Database.get_session()
        bag, e = find_bag_in_database(session, store_name, bag_name)
        if e:
            return e, e.code

        comment_model = RosbagComment()
        comment_model.from_swagger_model(comment)
        comment_model.user_id = user.uid
        comment_model.bag_id = bag.uid

        session.add(comment_model)
        session.commit()

        return comment_model.to_swagger_model()

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.BagCommentWrite)
def delete_bag_comment(store_name, bag_name, comment_id, user=None):  # noqa: E501
    """Post a comment

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str
    :param bag_name: Name of the bag
    :type bag_name: str
    :param comment_id: Comment identifier
    :type comment_id: int

    :rtype: None
    """
    try:
        session = Database.get_session()
        bag, e = find_bag_in_database(session, store_name, bag_name)
        if e:
            return e, e.code

        q = session.query(RosbagComment).filter(RosbagComment.uid == comment_id) # type: Query
        if q.count() != 1 or q.first().bag_id != bag.uid:
            return Error(code=404, message="Comment not found"), 404

        session.delete(q.first())
        session.commit()

        return "", 204

    except Exception as e:
        return handle_exception(e)


@auth.requires_auth_with_permission(Permissions.BagCommentRead)
def get_bag_comments(store_name, bag_name, user=None):  # noqa: E501
    """List comments from bag

     # noqa: E501

    :param store_name: Name of the store
    :type store_name: str
    :param bag_name: Name of the bag
    :type bag_name: str

    :rtype: List[Comment]
    """
    try:
        session = Database.get_session()
        bag, e = find_bag_in_database(session, store_name, bag_name)
        if e:
            return e, e.code

        return [p.to_swagger_model(user=user) for p in bag.comments]

    except Exception as e:
        return handle_exception(e)