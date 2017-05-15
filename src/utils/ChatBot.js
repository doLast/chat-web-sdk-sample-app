class ChatBot {
	composeResponse(msg) {
		return {
				display_name: 'Chat Bot',
				email: 'chat_bot@zenefits.com',
				member_type: 'agent',
				msg,
				nick: 'chat_bot',
				source: 'local',
				timestamp: Date.now(),
				type: 'chat.msg'
			}
	}
	handleInitialState(msg) {
		console.info('Handling initial state message');
		if (msg === 'help') {
			this.state = 'help';
			return this.composeResponse('How can I help you?');
		}
	}
	handleHelpState(msg) {
		console.info('Handling help state message');
		this.state = null;
		if (msg.match(/qle/i)) {
			return this.composeResponse('https://help.zenefits.com/Medical_Dental_Vision/Learn_About_Health_Insurance/Qualifying_Life_Events/01-Common_Qualifying_Life_Events/');
		}
	}

	response(chat) {
		if (!chat.member_type == 'visitor') {
			this.withHuman = true;
			return;
		}
		if (this.withHuman) {
			return;
		}

		console.info('Handling visitor message');

		if (!this.state) {
			return this.handleInitialState(chat.msg);
		} else if (this.state == 'help') {
			return this.handleHelpState(chat.msg);
		}
	}
}

export let chatBot = new ChatBot();
