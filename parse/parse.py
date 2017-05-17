import json
import requests

RULE_KEY_NAME = "key_name"
RULE_TITLE = "title"
RULE_CONTENT = "content"
RULE_SUBRULE = "subsections"


def generalDepartRule(rules):
	condition = [
		"and",
		[
			"eq",
			"@message",
			"agent"
		],
		[
			"eq",
			"@sender_type",
			"visitor"
		]
	]
	for rule in rules:
		condition.append([
			"not",
			[
				"hasTag",
				rule['tag']
			]
		])

	return [{
		"definition": {
			"event": "chat_message",
			"condition": condition,
			"actions": [
				[
					"setDepartment",
					1817723131
				],
				[
					"sendMessageToVisitor",
					"Customer Service",
					"Transfeting you to General Inquiry Department"
				]
			]
		},
		"enabled": True,
		"description": "Rule for human contact without tags",
		"name": "generalDepartRule"
	}]

def parseDepartmentRule(rule):
	return [{
		"definition": {
			"event": "chat_message",
			"condition": [
				"and",
				[
					"eq",
					"@message",
					"agent"
				],
				[
					"eq",
					"@sender_type",
					"visitor"
				],
				[
					"hasTag",
					rule['tag']
				]
			],
			"actions": [
				[
					"setDepartment",
					rule['departmentId']
				],
				[
					"sendMessageToVisitor",
					"Customer Service",
					"Transfeting you to {} Department".format(rule['departmentName'])
				]
			]
		},
		"enabled": True,
		"description": "Assign employee to agent in department {} due to tag {}".format(rule['departmentName'], rule['tag']),
		"name": "agent_tag_{}_department_{}".format(rule['tag'], rule['departmentName'])
	}]

def ruleTemplate(content, options, conditionString, name, description, tags=[], parentIndex=None, rootNode=False):
	if rootNode:
		event = 'chat_requested'
		condition = [
			"and",
			[
				"or",
				[
					"eq",
					"@visitor_requesting_chat",
					True
				]
			],
			[
				"not",
				[
					"firedBefore"
				]
			],
			[
				"eq",
				"@sender_type",
				"visitor"
			]
		]

	else:
		event = 'chat_message'
		condition = [
			"and",
			[
				"eq",
				"@message",
				conditionString
			],
			[
				"eq",
				"@sender_type",
				"visitor"
			]
		]

	actions = []
	if options:
		optionsWithIndex = []
		for i in xrange(len(options)):
			if parentIndex:
				optionsWithIndex.append("({parentIndex}.{currentIndex}) {title}".format(
					parentIndex=parentIndex,
					currentIndex=i + 1,
					title=options[i]
				))
			else:
				optionsWithIndex.append("({currentIndex}) {title}".format(
					currentIndex=i + 1,
					title=options[i]
				))

		action = [
			"sendMessageToVisitor",
			"Customer Service",
			content,
			"/".join(optionsWithIndex)
		]
		actions.append(action)
	else:
		action = [
			"sendMessageToVisitor",
			"Customer Service",
			content
		]
		actions.append(action)


	if tags:
		for tag in tags:
			actions.append([
				"addTag",
				tag
			])

	return {
		"definition": {
			"actions": actions,
			"event": event,
			"condition": condition
		},
		"enabled": True,
		"description": description,
		"name": name
	}


def _getRuleKey(rule):
	if RULE_KEY_NAME in rule:
		return rule[RULE_KEY_NAME]
	else:
		return rule[RULE_TITLE]

def parseRule(rule, parentRule, parentRuleIndex):
	content = rule[RULE_CONTENT]
	options = [_getRuleKey(subrule) for subrule in rule[RULE_SUBRULE]] if RULE_SUBRULE in rule else []
	conditionString = _getRuleKey(rule) if not parentRuleIndex else "({}) {}".format(parentRuleIndex, _getRuleKey(rule))
	description = rule[RULE_CONTENT]
	parsedRules = []
	if not parentRuleIndex:
		name = rule[RULE_TITLE]
		parsedRules.append(ruleTemplate(content, options, conditionString, name, description, rule.get('tags', []), parentIndex=parentRuleIndex, rootNode=True))

	name = _getRuleKey(rule)
	parsedRules.append(ruleTemplate(content, options, conditionString, name, description, rule.get('tags', []), parentIndex=parentRuleIndex))
	for i in xrange(len(rule.get(RULE_SUBRULE, []))):
		subRule = rule[RULE_SUBRULE][i]
		parsedRules += parseRule(subRule, rule, "{}.{}".format(parentRuleIndex, i + 1) if parentRuleIndex else "{}".format(i + 1))

	return parsedRules


def parseRuleFile(filename='rule.json'):
	finalRules = []

	with open(filename) as json_data:
		rules = json.load(json_data)
		msgRule = rules['messageRules']
		for rule in msgRule:
			finalRules += parseRule(rule, None, None)

		departmentRules = rules['departmentRules']
		for rule in departmentRules:
			finalRules += parseDepartmentRule(rule)

		finalRules += generalDepartRule(departmentRules)

	return finalRules

rules = parseRuleFile()

def submit(newTriggers):
	headers = {
		'Authorization': 'Basic Z3dhbmcrMjI0MzIzODUzODdAemVuZWZpdHMuY29tOmdQZE5WeEI5VyNtMjk+bS8=',
	}
	r = requests.get('https://www.zopim.com/api/v2/triggers', headers=headers)
	oldTriggers = r.json()
	for t in oldTriggers:
		print 'deleting', t['name']
		r = requests.delete('https://www.zopim.com/api/v2/triggers/{}'.format(t['name']), headers=headers)

	for t in newTriggers:
		print 'adding', t
		r = requests.post('https://www.zopim.com/api/v2/triggers', json=t, headers=headers)
		print r

rules = parseRuleFile()
print rules
submit(rules)
