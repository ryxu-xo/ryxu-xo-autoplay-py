"""
Tests for the event system.
"""

import pytest
import asyncio
from unittest.mock import Mock
from autoplay.events import AutoplayEventEmitter


@pytest.fixture
def event_emitter():
    """Create an event emitter for testing."""
    return AutoplayEventEmitter()


def test_event_emitter_creation(event_emitter):
    """Test event emitter creation."""
    assert event_emitter._listeners == {}


def test_event_emitter_on(event_emitter):
    """Test registering event listeners."""
    callback = Mock()
    event_emitter.on('test_event', callback)
    
    assert 'test_event' in event_emitter._listeners
    assert callback in event_emitter._listeners['test_event']


def test_event_emitter_off(event_emitter):
    """Test removing event listeners."""
    callback = Mock()
    event_emitter.on('test_event', callback)
    event_emitter.off('test_event', callback)
    
    assert callback not in event_emitter._listeners['test_event']


def test_event_emitter_off_nonexistent(event_emitter):
    """Test removing non-existent event listener."""
    callback = Mock()
    event_emitter.off('test_event', callback)  # Should not raise an error


def test_event_emitter_emit(event_emitter):
    """Test emitting events."""
    callback = Mock()
    event_emitter.on('test_event', callback)
    
    event_emitter.emit('test_event', 'arg1', 'arg2', key='value')
    
    callback.assert_called_once_with('arg1', 'arg2', key='value')


def test_event_emitter_emit_multiple_listeners(event_emitter):
    """Test emitting events to multiple listeners."""
    callback1 = Mock()
    callback2 = Mock()
    event_emitter.on('test_event', callback1)
    event_emitter.on('test_event', callback2)
    
    event_emitter.emit('test_event', 'arg1')
    
    callback1.assert_called_once_with('arg1')
    callback2.assert_called_once_with('arg1')


def test_event_emitter_emit_nonexistent_event(event_emitter):
    """Test emitting events to non-existent event."""
    # Should not raise an error
    event_emitter.emit('nonexistent_event', 'arg1')


def test_event_emitter_emit_async_callback(event_emitter):
    """Test emitting events to async callbacks."""
    async def async_callback(arg):
        return f"async_{arg}"
    
    event_emitter.on('test_event', async_callback)
    
    # This should create a task for the async callback
    event_emitter.emit('test_event', 'arg1')
    
    # Give the task time to run
    asyncio.run(asyncio.sleep(0.01))


def test_event_emitter_emit_callback_exception(event_emitter, capsys):
    """Test emitting events when callback raises an exception."""
    def error_callback(arg):
        raise ValueError("Test error")
    
    event_emitter.on('test_event', error_callback)
    
    # Should not raise an error, but should print error message
    event_emitter.emit('test_event', 'arg1')
    
    captured = capsys.readouterr()
    assert "[Event Error]" in captured.out


def test_event_emitter_remove_all_listeners_specific_event(event_emitter):
    """Test removing all listeners for a specific event."""
    callback1 = Mock()
    callback2 = Mock()
    event_emitter.on('test_event', callback1)
    event_emitter.on('test_event', callback2)
    event_emitter.on('other_event', Mock())
    
    event_emitter.remove_all_listeners('test_event')
    
    assert 'test_event' not in event_emitter._listeners
    assert 'other_event' in event_emitter._listeners


def test_event_emitter_remove_all_listeners_all_events(event_emitter):
    """Test removing all listeners for all events."""
    callback1 = Mock()
    callback2 = Mock()
    event_emitter.on('test_event', callback1)
    event_emitter.on('other_event', callback2)
    
    event_emitter.remove_all_listeners()
    
    assert event_emitter._listeners == {}
