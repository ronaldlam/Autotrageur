"""This module is responsible for any extra handling of the FCFCheckpoint.

Responsibilities:
1) Backwards-compatible pickling of the FCFCheckpoint

Please read the `pickle_fcf_checkpoint` and `unpickle_fcf_checkpoint` functions
carefully.  The two functions are both responsible for pickling/exporting and
restoring an FCFCheckpoint object in a way that is backwards-compatible.
"""
from bot.arbitrage.fcf.fcf_checkpoint import (CURRENT_FCF_CHECKPOINT_VERSION,
                                              FCFCheckpoint)


def _form_fcf_attr_map(checkpoint):
    """Forms an attribute map for the FCFCheckpoint object.

    Args:
        checkpoint (FCFCheckpoint): The checkpoint object to extract attributes
            from.

    Returns:
        dict: A map of all of the FCFCheckpoint attribute keys and values.
    """
    return {
        'config': checkpoint.config,
        'strategy_state': checkpoint.strategy_state,
        'dry_run_manager': checkpoint.dry_run_manager
    }

def pickle_fcf_checkpoint(checkpoint):
    """Helper function for copyreg.pickle.

    Takes a FCFCheckpoint object

    When used with copyreg.pickle, provides a level of indirection so that
    if we change the class being pickled (i.e. name change), deserializing will
    still function.

    Instructions when changing checkpoint versions:
    - In fcf_checkpoint.py, point `CURRENT_FCF_CHECKPOINT_VERSION` to the
    new version.
    - Make changes to `unpickle_fcf_checkpoint`

    Reference:
    - Effective Python Chapter 6, Item 44 (Make pickle Reliable with copyreg)

    Args:
        checkpoint (FCFCheckpoint): The FCFCheckpoint object to pickle.

    Returns:
        tuple: A tuple containing the unpickling checkpoint method and an inner
            tuple of key/value pairings of the checkpoint's attributes (and
            any additional kwargs such as version).
    """
    attr_map = _form_fcf_attr_map(checkpoint)
    attr_map['version'] = CURRENT_FCF_CHECKPOINT_VERSION
    return unpickle_fcf_checkpoint, (attr_map,)


def unpickle_fcf_checkpoint(kwargs):
    """A wrapper function which unpacks parameters and feeds to restored object
    constructor.

    Instructions when changing checkpoint versions:
    - Make any necessary adjustments in this method.
    - For different versions, we can pop items off the kwargs if that version
    did not have a particular attribute.  For example, if version 1 did not
    have a 'speed_run' attribute:

    ...
    version = kwargs.pop('version', 1)  # 1 is the default version if no version attribute
    if version == 1:
        kwargs.pop('speed_run')
    return FCFCheckpoint(**kwargs)
    ...


    Reference:
    - Effective Python Chapter 6, Item 44 (Make pickle Reliable with copyreg)

    NOTE:
    - Path to this function can NOT change as it must remain in the same
    path for deserializing in the future.
    - Attributes must match the current constructor's attributes.  This will
    require popping off any extra 'metadata'-like attributes such as 'version'
    before sending **kwargs to the constructor.

    Args:
        kwargs (dict): A map of the serialized FCFCheckpoint's attributes and
            any extra attributes such as 'version'.

    Returns:
        FCFCheckpoint: An FCFCheckpoint object, restored with the serialized
            attributes.
    """
    version = kwargs.pop('version', 1)
    # In the future, logic with different versions will be done here.
    return FCFCheckpoint(**kwargs)
