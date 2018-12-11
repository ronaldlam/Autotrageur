"""This module is responsible for any extra handling of the CCCheckpoint.

Responsibilities:
1) Backwards-compatible pickling of the CCCheckpoint

Please read the `pickle_cc_checkpoint` and `unpickle_cc_checkpoint` functions
carefully.  The two functions are both responsible for pickling/exporting and
restoring an CCCheckpoint object in a way that is backwards-compatible.
"""
from autotrageur.bot.arbitrage.cc.checkpoint import (CURRENT_CC_CHECKPOINT_VERSION,
                                                          CCCheckpoint)
from fp_libs.utilities import version_convert_to_compare as v_convert


def _form_cc_attr_map(checkpoint):
    """Forms an attribute map for the CCCheckpoint object.

    Args:
        checkpoint (CCCheckpoint): The checkpoint object to extract attributes
            from.

    Returns:
        dict: A map of all of the CCCheckpoint attribute keys and values.
    """
    return {
        'config': checkpoint.config,
        'strategy_state': checkpoint.strategy_state,
        'stat_tracker': checkpoint.stat_tracker
    }

def pickle_cc_checkpoint(checkpoint):
    """Helper function for copyreg.pickle.

    Takes a CCCheckpoint object

    When used with copyreg.pickle, provides a level of indirection so that
    if we change the class being pickled (i.e. name change), deserializing will
    still function.

    Instructions when changing checkpoint versions:
    - In cc_checkpoint.py, make sure `CURRENT_CC_CHECKPOINT_VERSION` is the
    new version.
    - Make changes to `unpickle_cc_checkpoint`

    Reference:
    - Effective Python Chapter 6, Item 44 (Make pickle Reliable with copyreg)

    Args:
        checkpoint (CCCheckpoint): The CCCheckpoint object to pickle.

    Returns:
        tuple: A tuple containing the unpickling checkpoint method and an inner
            tuple of key/value pairings of the checkpoint's attributes (and
            any additional kwargs such as version).
    """
    attr_map = _form_cc_attr_map(checkpoint)
    attr_map['version'] = CURRENT_CC_CHECKPOINT_VERSION
    return unpickle_cc_checkpoint, (attr_map,)


def unpickle_cc_checkpoint(kwargs):
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
    return CCCheckpoint(**kwargs)
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
        kwargs (dict): A map of the serialized CCCheckpoint's attributes and
            any extra attributes such as 'version'.

    Returns:
        CCCheckpoint: An CCCheckpoint object, restored with the serialized
            attributes.
    """
    version = kwargs.pop('version', '1')
    # In the future, logic with different versions will be done here.
    if v_convert(version) < v_convert('1.1.2'):
        # CCCheckpoint changed to contain a StatTracker object instead of
        # a DryRunManager.  We just pop off the DryRunManager to make sure that
        # the CCCheckpoint at least constructs correctly.
        kwargs.pop('dry_run_manager', None)
    return CCCheckpoint(**kwargs)
