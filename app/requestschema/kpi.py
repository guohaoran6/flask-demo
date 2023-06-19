#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Kpi entity object schema."""

kpi_create_request_schema = {

    "type": "object",
    "properties": {
        "based_on": {
            "type": "string",
            "enum": [
                "overall",
                "session",
                "easy_id",
                "member_id"
            ],
        },
        "kpi_definitions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kpi_conditions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "condition_type": {
                                    "type": "string",
                                    "enum": [
                                        "url",
                                        "custom_parameter",
                                        "add_to_cart",
                                        "conversion_url",
                                        "conversion_custom_parameter",
                                        "conversion_add_to_cart",
                                        "r2d2"
                                    ],
                                },
                                "conditions": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "domain": {
                                                "type": "string"

                                            },
                                            "operator": {
                                                "type": "string",
                                                "enum": [
                                                    "equal",
                                                    "ends_with",
                                                    "starts_with",
                                                    "like"
                                                ]

                                            },
                                            "paths": {
                                                "items": {
                                                    "type": "string"
                                                },
                                                "type": "array"
                                            }
                                        }

                                    }

                                }
                            },
                            "required": ["condition_type"]

                        },

                    },
                    "kpi_definition_name": {
                        "type": "string",
                        "pattern": "^\\S*$",
                        "maxLength": 200,
                        "minLength": 5
                    },
                    "kpi_type": {
                        "type": "string",
                        "enum": [
                            "conversion",
                            "click",
                            "clickThroughConversion",
                            "custom"
                        ],
                    },
                    "main_kpi": {
                        "type": "boolean"
                    },
                    "pattern_name": {
                        "type": "string"
                    }
                },
                "required": ["kpi_definition_name", "main_kpi"]
            }
        }
    },
    "required": ["based_on", "kpi_definitions"]
}

kpi_update_request_schema = {

    "type": "object",
    "properties": {
        "based_on": {
            "type": "string",
            "enum": [
                "overall",
                "session",
                "easy_id",
                "member_id"
            ],
        },
        "kpi_definitions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kpi_conditions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "condition_type": {
                                    "type": "string",
                                    "enum": [
                                        "url",
                                        "custom_parameter",
                                        "add_to_cart",
                                        "conversion_url",
                                        "conversion_custom_parameter",
                                        "conversion_add_to_cart",
                                        "r2d2"
                                    ],
                                },
                                "conditions": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "domain": {
                                                "type": "string"

                                            },
                                            "operator": {
                                                "type": "string",
                                                "enum": [
                                                    "equal",
                                                    "ends_with",
                                                    "starts_with",
                                                    "like"
                                                ]

                                            },
                                            "paths": {
                                                "items": {
                                                    "type": "string"
                                                },
                                                "type": "array"
                                            }
                                        }

                                    }

                                }
                            },
                            "required": ["condition_type"]

                        },

                    },
                    "kpi_definition_name": {
                        "type": "string",
                        "pattern": "^\\S*$",
                        "maxLength": 200,
                        "minLength": 5
                    },
                    "kpi_type": {
                        "type": "string",
                        "enum": [
                            "conversion",
                            "click",
                            "clickThroughConversion",
                            "custom"
                        ],
                    },
                    "main_kpi": {
                        "type": "boolean"
                    },
                    "pattern_name": {
                        "type": "string"
                    }
                },
                "required": ["kpi_definition_name", "main_kpi"]
            }
        }
    },
    "required": ["based_on", "kpi_definitions"]
}

kpi_setting_schema = {

    "type": "object",
    "properties": {
        "based_on": {
            "type": "string",
            "enum": [
                "overall",
                "session",
                "easy_id",
                "member_id"
            ],
        },
        "kpi_definitions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "kpi_conditions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "condition_type": {
                                    "type": "string",
                                    "enum": [
                                        "url",
                                        "custom_parameter",
                                        "add_to_cart",
                                        "conversion_url",
                                        "conversion_custom_parameter",
                                        "conversion_add_to_cart",
                                        "r2d2"
                                    ],
                                },
                                "conditions": {
                                    "type": "array",
                                    "items": {
                                        "type": "object",
                                        "properties": {
                                            "domain": {
                                                "type": "string"

                                            },
                                            "operator": {
                                                "type": "string",
                                                "enum": [
                                                    "equal",
                                                    "ends_with",
                                                    "starts_with",
                                                    "like"
                                                ]

                                            },
                                            "paths": {
                                                "items": {
                                                    "type": "string"
                                                },
                                                "type": "array"
                                            }
                                        }

                                    }

                                }
                            },
                            "required": ["condition_type"]

                        },

                    },
                    "kpi_definition_name": {
                        "type": "string",
                        "pattern": "^\\S*$",
                        "maxLength": 200,
                        "minLength": 5
                    },
                    "kpi_type": {
                        "type": "string",
                        "enum": [
                            "conversion",
                            "click",
                            "clickThroughConversion",
                            "custom"
                        ],
                    },
                    "main_kpi": {
                        "type": "boolean"
                    },
                    "pattern_name": {
                        "type": "string"
                    }
                },
                "required": ["kpi_definition_name", "main_kpi"]

            }

        }
    },
    "required": ["based_on","kpi_definitions"]
}
