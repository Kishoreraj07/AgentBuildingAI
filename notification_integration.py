"""
Integration module for adding notification popups to the main process workflow.
This module provides functions to be called from main_process.py to show notifications.
"""

from notification_popups import (
    show_task_generated_notification,
    show_detail_mode_started_notification, 
    show_detail_mode_completed_notification,
    add_popup_to_tracker,
    cleanup_popups
)

def integrate_task_generation_notifications(main_app_instance):
    """
    Integrate notification popups into the main application's task generation workflow.
    This function patches the existing methods to add notification calls.
    """
    
    # Store original methods
    original_process_requirement = main_app_instance.process_requirement
    original_process_file_requirement = main_app_instance.process_file_requirement
    original_detail_mode_validation = main_app_instance.start_detail_mode_validation
    
    def enhanced_process_requirement(self):
        """Enhanced process_requirement with notification popup"""
        try:
            # Call original method
            result = original_process_requirement()
            
            # Show task generation popup after successful processing
            if hasattr(self, 'req_class') and self.req_class:
                task_count = len(self.req_class)
                popup = show_task_generated_notification(task_count, parent=self)
                add_popup_to_tracker(popup)
                print(f"✅ Showed task generation notification: {task_count} steps")
            
            return result
        except Exception as e:
            print(f"Error in enhanced_process_requirement: {e}")
            return original_process_requirement()
    
    def enhanced_process_file_requirement(self):
        """Enhanced process_file_requirement with notification popup"""
        try:
            # Call original method
            result = original_process_file_requirement()
            
            # Show task generation popup after successful file processing
            if hasattr(self, 'req_class') and self.req_class:
                task_count = len(self.req_class)
                popup = show_task_generated_notification(task_count, parent=self)
                add_popup_to_tracker(popup)
                print(f"✅ Showed file processing notification: {task_count} steps")
            
            return result
        except Exception as e:
            print(f"Error in enhanced_process_file_requirement: {e}")
            return original_process_file_requirement()
    
    def enhanced_detail_mode_validation(self):
        """Enhanced detail mode validation with start notification"""
        try:
            # Show detail mode started notification
            popup = show_detail_mode_started_notification(parent=self)
            add_popup_to_tracker(popup)
            print(" Showed detail mode started notification")
            
            # Call original method
            return original_detail_mode_validation()
        except Exception as e:
            print(f"Error in enhanced_detail_mode_validation: {e}")
            return original_detail_mode_validation()
    
    # Patch the methods
    main_app_instance.process_requirement = lambda: enhanced_process_requirement(main_app_instance)
    main_app_instance.process_file_requirement = lambda: enhanced_process_file_requirement(main_app_instance)
    main_app_instance.start_detail_mode_validation = lambda: enhanced_detail_mode_validation(main_app_instance)
    
    print("✅ Notification integration completed")


def show_detail_mode_completion_popup(main_app_instance):
    """Show detail mode completion popup"""
    try:
        popup = show_detail_mode_completed_notification(parent=main_app_instance)
        add_popup_to_tracker(popup)
        print("✅ Showed detail mode completion notification")
        return popup
    except Exception as e:
        print(f"Error showing detail mode completion popup: {e}")
        return None


def cleanup_all_popups():
    """Clean up all notification popups"""
    try:
        cleanup_popups()
        print("✅ All notification popups cleaned up")
    except Exception as e:
        print(f"Error cleaning up popups: {e}")
