# Fix for NEX-123: Adjusted login button CSS
# Commit: abc123 - Fix login button alignment on mobile devices

def apply_mobile_styles(button_element, screen_width):
    """
    Apply mobile-specific styles to center the login button
    on screens smaller than 480px.
    
    Args:
        button_element: The DOM element for the login button
        screen_width: Current screen width in pixels
    """
    if screen_width < 480:
        button_element.style.marginLeft = 'auto'
        button_element.style.marginRight = 'auto'
        button_element.style.display = 'block'
        button_element.style.width = '100%'
        button_element.style.maxWidth = '300px'
    else:
        # Reset for larger screens
        button_element.style.marginLeft = ''
        button_element.style.marginRight = ''
        button_element.style.display = 'inline-block'
        button_element.style.width = 'auto'

def get_responsive_button_class(screen_width):
    """Return appropriate CSS class based on screen width"""
    return 'btn-mobile' if screen_width < 480 else 'btn-desktop'

# CSS classes applied
MOBILE_STYLES = {
    'margin': '0 auto',
    'display': 'block',
    'width': '100%',
    'max-width': '300px'
}
