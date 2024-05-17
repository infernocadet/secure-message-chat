// This document includes all the friends list functionality, 
// including adding and removing friends

// adding friend function
document.getElementById('friendrequestForm').addEventListener('submit', function(event) {
    event.preventDefault(); // prevent form from submitting the traditional way

    let friendUsername = document.getElementById('friendUsername').value;
    let currentUsername = "{{ username }}";

    // add in error handling to prevent users from adding themselves
    if (friendUsername == currentUsername) {
        document.getElementById('friendRequestMessage').textContent = "Can't add yourself!";
        document.getElementById('friendRequestMessage').style.display = 'block';
        return new Error("Error message");
    }
    
    // construct url for the post event
    let addFriendURL = "{{ url_for('add_friend') }}";

    // use axios to send post request
    axios.post(addFriendURL, {
        current_user: currentUsername,
        friend_user: friendUsername
    })
    .then(function (response) {

        console.log(response.data);
        document.getElementById('friendRequestMessage').textContent = "Friend request sent!";
        document.getElementById('friendRequestMessage').style.display = 'block';
    })
    .catch(function (error) {
        console.error('Error:', error)

        // check if error response contains data
        if (error.response && error.response.data){
            // display error message
            document.getElementById('friendRequestMessage').textContent = error.response.data.error;
        } else {
            document.getElementById('friendRequestMessage').textContent = "An error occurred while sending the friend request.";
        }
        document.getElementById('friendRequestMessage').style.display = 'block';
    });
});

// function to accept a friend request
function acceptfriendRequest(requestID, element) {
    let acceptURL = "{{ url_for('accept_friend_request') }}"
    axios.post(acceptURL, {
        request_id: requestID
    })
    .then(function (response) {

        // check if response contains an error
        if (response.data.error){

            // display error
            document.getElementById('requestResponse').textContent = response.data.error;
            document.getElementById('requestResponse').style.display = 'block';

        } else {

            // on success, remove request from list
            element.closest('li').remove();

            // check if any more friend requests
            let incomingRequestsList = document.getElementById('incomingRequestsList');
            if (incomingRequestsList && incomingRequestsList.children.length === 0){
                // if none, display no incoming requests
                noIncomingRequestsMessage.style.display = 'block';
            }

            // success message
            console.log(response.data);
            document.getElementById('requestResponse').textContent = "You accepted the request!";
            document.getElementById('requestResponse').style.display = 'block';
        }
        
    })
    .catch(function (error){
        console.error('Error:', error)
        document.getElementById('requestResponse').textContent = error;
        document.getElementById('requestResponse').style.display = 'block';
    });
};

// function to reject a friend request
function rejectfriendRequest(requestID, element) {
    let rejectURL = "{{ url_for('reject_friend_request') }}"
    axios.post(rejectURL, {
        request_id: requestID
    })
    .then(function (response) {

        // on success, remove friend request from UI
        element.closest('li').remove();

        // check if any more friend requests
        let incomingRequestsList = document.getElementById('incomingRequestsList');
        if (incomingRequestsList && incomingRequestsList.children.length === 0){
            // if none, display no incoming requests
            noIncomingRequestsMessage.style.display = 'block';
        }

        console.log(response.data);
        document.getElementById('requestResponse').textContent = "You rejected the request!";
        document.getElementById('requestResponse').style.display = 'block';

    })
    .catch(function (error){
        console.error('Error:', error)
        document.getElementById('requestResponse').textContent = "reject error";
        document.getElementById('requestResponse').style.display = 'block';
    });
};

function removeFriend(friendUsername) {
    let removeFriendURL = "{{ url_for('remove_friend') }}";

    axios.post(removeFriendURL, {
        friend_username: friendUsername
    })
    .then(function(response) {
        console.log(response.data);
        if (response.data.success) {
            // Remove friend from the list
            let friendElement = document.getElementById('friend-' + friendUsername);
            if (friendElement) {
                friendElement.remove();
            }
        } else {
            console.error(response.data.error);
        }
    })
    .catch(function(error) {
        console.error('Error:', error);
    });
};