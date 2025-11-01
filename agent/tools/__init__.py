"""
ClaudeVoice Tools Package
Collection of tool functions for the voice agent
"""

from .weather import (
    weather_tool,
    weather_forecast,
    check_weather_conditions
)

from .calendar import (
    calendar_tool,
    check_availability,
    list_appointments,
    cancel_appointment,
    reschedule_appointment
)

from .database import (
    database_query,
    get_customer_info,
    check_inventory,
    update_database
)

from .voicemail import (
    detect_voicemail,
    leave_voicemail_message,
    analyze_voicemail_greeting,
    wait_for_beep,
    VoicemailHandler
)

__all__ = [
    # Weather tools
    'weather_tool',
    'weather_forecast',
    'check_weather_conditions',

    # Calendar tools
    'calendar_tool',
    'check_availability',
    'list_appointments',
    'cancel_appointment',
    'reschedule_appointment',

    # Database tools
    'database_query',
    'get_customer_info',
    'check_inventory',
    'update_database',

    # Voicemail tools
    'detect_voicemail',
    'leave_voicemail_message',
    'analyze_voicemail_greeting',
    'wait_for_beep',
    'VoicemailHandler'
]