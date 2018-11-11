# -*- coding: utf-8 -*-
"""
A simple vulkan debugger. It prints vulkan warning and error in the stdout.
"""

from . import vk
from ctypes import byref
from enum import IntFlag
import weakref


class Debugger(object):
    """
     A high level wrapper over the debug_utils vulkan extension. When an error is catched, it is printed somewhere
    """

    def __init__(self, api, instance):
        self.api = weakref.ref(api)
        self.instance = instance
        self.debug_report_callback = None
        self.callback_fn = None
        self.callbacks = [print]

        f = MessageSeverity
        self.report_flags = f.Information | f.Warning | f.Error

    @property
    def running(self):
        return self.debug_report_callback is not None

    def format_debug(self, message_severity, message_type, callback_data, user_data):
        message_severity = MessageSeverity(message_severity).name
        message_type = MessageType(message_type).name
        
        data = callback_data.contents
        message = data.message[::].decode()
        full_message = f"{message_severity}/{message_type} -> {message}"
       
        for callback in self.callbacks:
            callback(full_message)

        return 0

    def start(self):
        """ Start the debugger """
        if self.running:
            self.stop()

        api, instance = self.api(), self.instance
        callback_fn = vk.FnDebugUtilsMessengerCallbackEXT(lambda *args: self.format_debug(*args))
        
        create_info = vk.DebugUtilsMessengerCreateInfoEXT(
            type = vk.STRUCTURE_TYPE_DEBUG_UTILS_MESSENGER_CREATE_INFO_EXT,
            next = None,
            flags = 0,
            message_severity = self.report_flags,
            message_type =  vk.DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT | vk.DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT,
            user_callback = callback_fn,
            user_data = None
        )

        debug_report_callback = vk.DebugUtilsMessengerEXT(0)
        result = api.CreateDebugUtilsMessengerEXT(
            instance, byref(create_info), None, byref(debug_report_callback)
        )

        if result != vk.SUCCESS:
            raise RuntimeError(f"Failed to start the vulkan debug utils report: {result}")

        self.callback_fn = callback_fn
        self.debug_report_callback = debug_report_callback

    def stop(self):
        """ Stop the debugger """
        if not self.running:
            return

        api, instance = self.api(), self.instance
        api.DestroyDebugUtilsMessengerEXT(instance, self.debug_report_callback, None)
        self.debug_report_callback = None
        self.callback_fn = None


class MessageSeverity(IntFlag):
    Verbose = vk.DEBUG_UTILS_MESSAGE_SEVERITY_VERBOSE_BIT_EXT
    Information = vk.DEBUG_UTILS_MESSAGE_SEVERITY_INFO_BIT_EXT
    Warning = vk.DEBUG_UTILS_MESSAGE_SEVERITY_WARNING_BIT_EXT
    Error = vk.DEBUG_UTILS_MESSAGE_SEVERITY_ERROR_BIT_EXT

class MessageType(IntFlag):
    General = vk.DEBUG_UTILS_MESSAGE_TYPE_GENERAL_BIT_EXT 
    Performance = vk.DEBUG_UTILS_MESSAGE_TYPE_PERFORMANCE_BIT_EXT
    Validation = vk.DEBUG_UTILS_MESSAGE_TYPE_VALIDATION_BIT_EXT
