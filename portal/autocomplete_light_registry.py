import autocomplete_light
from models import ElsterMeterTrack, ElsterRma

# This will generate a ElsterMeterTrack class
autocomplete_light.register(ElsterMeterTrack,
    # Just like in ModelAdmin.search_fields
    search_fields=['^elster_serial_number', 'meter_barcode',],
    attrs={
        # This will set the input placeholder attribute:
        'placeholder': 'Elster Meter Track',
        # This will set the yourlabs.Autocomplete.minimumCharacters
        # options, the naming conversion is handled by jQuery
        'data-autocomplete-minimum-characters': 1,
    },
    # This will set the data-widget-maximum-values attribute on the
    # widget container element, and will be set to
    # yourlabs.Widget.maximumValues (jQuery handles the naming
    # conversion).
    widget_attrs={
        'data-widget-maximum-values': 4,
        # Enable modern-style widget !
        'class': 'modern-style',
    },
)

# This will generate a ElsterRma class
autocomplete_light.register(ElsterRma,
    # Just like in ModelAdmin.search_fields
    search_fields=['^number'],
    attrs={
        # This will set the input placeholder attribute:
        'placeholder': 'Elster RMA',
        # This will set the yourlabs.Autocomplete.minimumCharacters
        # options, the naming conversion is handled by jQuery
        'data-autocomplete-minimum-characters': 1,
    },
    # This will set the data-widget-maximum-values attribute on the
    # widget container element, and will be set to
    # yourlabs.Widget.maximumValues (jQuery handles the naming
    # conversion).
    widget_attrs={
        'data-widget-maximum-values': 4,
        # Enable modern-style widget !
        'class': 'modern-style',
    },
)